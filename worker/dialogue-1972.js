// ============================================================================
// Cloudflare Worker — proxy Mistral pour les dialogues IA + synthèse vocale
// Formation IGEDD · Anse-de-Goulven · Littoraux ultramarins (réf. 014917-02)
// ============================================================================
//
// Routes :
//   POST /          → chat (Mistral chat completions, format Anthropic ↔ Mistral)
//                     supporte désormais la VISION (blocs image → Pixtral)
//   POST /tts       → text-to-speech (Voxtral, retourne MP3 binaire)
//   GET|POST /voices→ liste des voix Mistral (lecture seule, public)
//
// DURCISSEMENT (vs version initiale) :
//   1. Application stricte de l'origine : un navigateur d'un autre site est
//      rejeté en 403. Les requêtes sans origine (file://, curl) passent mais
//      sont soumises au rate-limiting.
//   2. Rate-limiting par IP via le binding natif Workers (voir wrangler.toml).
//      Si le binding est absent, le worker fonctionne sans (dégradé).
//   3. max_tokens plafonné, taille de payload bornée.
//   4. Vision : traduction des blocs image Anthropic → format Mistral + modèle
//      Pixtral, pour activer l'analyse d'images côtières.
//
// CLÉ : MISTRAL_API_KEY est un secret (Settings → Variables and Secrets,
//       ou `wrangler secret put MISTRAL_API_KEY`). Jamais en clair dans le code.
// ============================================================================

const ALLOWED_ORIGINS = [
  'https://boris29-env.github.io',   // site GitHub Pages de la plateforme
  'http://localhost:8000',
  'http://127.0.0.1:8000',
  'http://localhost:5500',
  'http://127.0.0.1:5500',
];

const MISTRAL_CHAT_MODEL   = 'mistral-medium-latest';  // texte
const MISTRAL_VISION_MODEL = 'pixtral-12b-2409';       // images (analyse côtière)
const MISTRAL_TTS_MODEL    = 'voxtral-mini-tts-2603';  // synthèse vocale

// Garde-fous de coût
const MAX_TOKENS_CAP   = 1500;   // plafond dur quel que soit le max_tokens demandé
const MAX_BODY_BYTES   = 5_000_000; // 5 Mo (une image base64 reste sous cette limite)
const MAX_TTS_CHARS    = 2000;

// ---------------------------------------------------------------------------
// CORS
// ---------------------------------------------------------------------------
function resolveAllowOrigin(origin) {
  if (ALLOWED_ORIGINS.includes(origin)) return origin;
  if (!origin || origin === 'null') return '*'; // dev : file:// ou requête sans origine
  return ALLOWED_ORIGINS[0];                     // autre site : en-tête neutre (et 403 en amont)
}

function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin': resolveAllowOrigin(origin),
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
  };
}

function jsonResponse(body, status, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
  });
}

// ---------------------------------------------------------------------------
// Anthropic → Mistral : traduction du contenu (texte + images)
// ---------------------------------------------------------------------------
function toMistralContent(content) {
  if (typeof content === 'string') return content;
  if (!Array.isArray(content)) return '';
  const parts = [];
  for (const block of content) {
    if (!block || !block.type) continue;
    if (block.type === 'text' && typeof block.text === 'string') {
      parts.push({ type: 'text', text: block.text });
    } else if (block.type === 'image' && block.source) {
      const s = block.source;
      let url = null;
      if (s.type === 'base64' && s.data) {
        url = `data:${s.media_type || 'image/jpeg'};base64,${s.data}`;
      } else if (s.type === 'url' && s.url) {
        url = s.url;
      }
      if (url) parts.push({ type: 'image_url', image_url: url });
    } else if (block.type === 'image_url') {
      parts.push(block); // déjà au format Mistral
    }
  }
  return parts;
}

// ---------------------------------------------------------------------------
// HANDLER : CHAT (route /)
// ---------------------------------------------------------------------------
async function handleChat(request, env, origin) {
  const anthropicBody = await request.json();

  const mistralMessages = [];
  if (anthropicBody.system) {
    mistralMessages.push({ role: 'system', content: anthropicBody.system });
  }

  let hasImage = false;
  if (Array.isArray(anthropicBody.messages)) {
    for (const m of anthropicBody.messages) {
      if (!m || !m.role) continue;
      const content = toMistralContent(m.content);
      const empty = (typeof content === 'string') ? content.length === 0 : content.length === 0;
      if (empty) continue;
      if (Array.isArray(content) && content.some(p => p.type === 'image_url')) hasImage = true;
      mistralMessages.push({ role: m.role, content });
    }
  }

  if (mistralMessages.filter(m => m.role !== 'system').length === 0) {
    return jsonResponse({ error: 'Aucun message exploitable', _proxy: 'mistral-chat' }, 400, origin);
  }

  const mistralPayload = {
    model: hasImage ? MISTRAL_VISION_MODEL : MISTRAL_CHAT_MODEL,
    messages: mistralMessages,
    max_tokens: Math.min(Number(anthropicBody.max_tokens) || 400, MAX_TOKENS_CAP),
    temperature: typeof anthropicBody.temperature === 'number' ? anthropicBody.temperature : 0.7,
  };

  const upstream = await fetch('https://api.mistral.ai/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${env.MISTRAL_API_KEY}`,
      'Accept': 'application/json',
    },
    body: JSON.stringify(mistralPayload),
  });

  if (!upstream.ok) {
    const errorText = await upstream.text();
    let errorDetail = errorText;
    try {
      const parsed = JSON.parse(errorText);
      errorDetail = parsed.message || parsed.error?.message || errorText;
    } catch (_) {}
    return jsonResponse({
      error: 'Erreur Mistral chat', status: upstream.status, detail: errorDetail,
      _proxy: 'mistral-chat', _model: mistralPayload.model,
    }, upstream.status, origin);
  }

  const mistralResponse = await upstream.json();
  const replyText = mistralResponse?.choices?.[0]?.message?.content || '';

  return jsonResponse({
    content: [{ type: 'text', text: replyText }],
    model: mistralResponse?.model || mistralPayload.model,
    usage: mistralResponse?.usage || {},
    _proxy: hasImage ? 'mistral-vision' : 'mistral-chat',
  }, 200, origin);
}

// ---------------------------------------------------------------------------
// HANDLER : TTS (route /tts)
// ---------------------------------------------------------------------------
async function handleTTS(request, env, origin) {
  const body = await request.json();
  const text = (body.text || '').trim();
  const voiceId = body.voice_id || body.voice || '';

  if (!text) return jsonResponse({ error: 'Champ "text" requis' }, 400, origin);
  if (!voiceId) {
    return jsonResponse({
      error: 'Champ "voice_id" requis — créer une voix dans Mistral Studio (Audio → Voices)',
    }, 400, origin);
  }
  if (text.length > MAX_TTS_CHARS) {
    return jsonResponse({ error: 'Texte trop long (limite ' + MAX_TTS_CHARS + ' caractères)', length: text.length }, 400, origin);
  }

  const voxtralPayload = {
    model: MISTRAL_TTS_MODEL,
    input: text,
    voice_id: voiceId,
    response_format: 'mp3',
  };

  const upstream = await fetch('https://api.mistral.ai/v1/audio/speech', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${env.MISTRAL_API_KEY}`,
      'Accept': 'application/json',
    },
    body: JSON.stringify(voxtralPayload),
  });

  if (!upstream.ok) {
    const errorText = await upstream.text();
    let errorDetail = errorText;
    try {
      const parsed = JSON.parse(errorText);
      errorDetail = parsed.message || parsed.error?.message || errorText;
    } catch (_) {}
    return jsonResponse({ error: 'Erreur Voxtral TTS', status: upstream.status, detail: errorDetail }, upstream.status, origin);
  }

  const data = await upstream.json();
  const b64 = data.audio_data || data.audio || '';
  if (!b64) return jsonResponse({ error: 'Réponse TTS sans audio_data', detail: data }, 502, origin);

  const binary = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  return new Response(binary, {
    status: 200,
    headers: { 'Content-Type': 'audio/mpeg', 'Cache-Control': 'no-store', ...corsHeaders(origin) },
  });
}

// ---------------------------------------------------------------------------
// HANDLER : LIST VOICES (route /voices)
// ---------------------------------------------------------------------------
async function handleListVoices(env, origin) {
  const upstream = await fetch('https://api.mistral.ai/v1/audio/voices', {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${env.MISTRAL_API_KEY}`, 'Accept': 'application/json' },
  });

  if (!upstream.ok) {
    const errorText = await upstream.text();
    return jsonResponse({ error: 'Erreur Mistral list voices', status: upstream.status, detail: errorText }, upstream.status, origin);
  }

  const data = await upstream.json();
  const list = (Array.isArray(data) ? data : (data.items || data.voices || data.data || []));
  const simplified = list.map(v => ({
    id: v.id || v.voice_id || v.uuid,
    name: v.name || v.label || '',
    gender: v.gender || '',
    languages: v.languages || [],
    is_custom: !!v.user_id,
    created_at: v.created_at || v.created || '',
  }));

  return new Response(JSON.stringify({ voices: simplified, raw: data }, null, 2), {
    status: 200,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*' },
  });
}

// ---------------------------------------------------------------------------
// Rate-limiting (binding natif Workers, dégradé si absent)
// ---------------------------------------------------------------------------
async function rateLimited(env, request) {
  if (!env.RATE_LIMITER || typeof env.RATE_LIMITER.limit !== 'function') return false; // pas de binding → on ne bloque pas
  const ip = request.headers.get('CF-Connecting-IP') || 'anon';
  try {
    const { success } = await env.RATE_LIMITER.limit({ key: ip });
    return !success;
  } catch (_) {
    return false;
  }
}

// ---------------------------------------------------------------------------
// ROUTEUR PRINCIPAL
// ---------------------------------------------------------------------------
export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/$/, '');

    // Preflight CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    // Application de l'origine : un navigateur d'un autre site (origine réelle
    // non autorisée) est rejeté. file:// (origine "null") et requêtes sans
    // origine passent — elles restent bornées par le rate-limiting.
    const isCrossSiteBrowser = origin && origin !== 'null';
    if (isCrossSiteBrowser && !ALLOWED_ORIGINS.includes(origin)) {
      return jsonResponse({ error: 'Origine non autorisée', origin }, 403, origin);
    }

    // /voices : lecture seule
    if (path === '/voices') {
      if (!env.MISTRAL_API_KEY) return jsonResponse({ error: 'Clé API non configurée' }, 500, origin);
      try { return await handleListVoices(env, origin); }
      catch (err) { return jsonResponse({ error: 'Erreur', detail: String(err) }, 502, origin); }
    }

    if (request.method !== 'POST') {
      return jsonResponse({ error: 'Méthode non autorisée — utiliser POST' }, 405, origin);
    }

    if (!env.MISTRAL_API_KEY) {
      return jsonResponse({ error: 'Clé API Mistral non configurée — ajouter MISTRAL_API_KEY dans Settings → Variables and Secrets' }, 500, origin);
    }

    // Rate-limiting
    if (await rateLimited(env, request)) {
      return jsonResponse({ error: 'Trop de requêtes — réessayez dans une minute.' }, 429, origin);
    }

    // Borne de taille
    const cl = Number(request.headers.get('Content-Length') || 0);
    if (cl && cl > MAX_BODY_BYTES) {
      return jsonResponse({ error: 'Requête trop volumineuse', max_bytes: MAX_BODY_BYTES }, 413, origin);
    }

    try {
      if (path === '/tts') return await handleTTS(request, env, origin);
      return await handleChat(request, env, origin);
    } catch (err) {
      return jsonResponse({ error: 'Erreur du proxy', path, detail: String(err && err.message || err) }, 502, origin);
    }
  },
};
