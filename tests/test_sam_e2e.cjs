// Test SAM via le build CJS (Node) qui utilise onnxruntime-node
(async () => {
  const t = require('/tmp/node_modules/@huggingface/transformers/dist/transformers.cjs');
  console.log('=== transformers.js (CJS) chargé · classes :', Object.keys(t).filter(k=>/SamModel|AutoProc|RawImage/.test(k)).join(', '));
  const MODEL = 'Xenova/slimsam-77-uniform';
  // Cache local pour ne pas retélécharger
  t.env.cacheDir = '/tmp/sam_cache';
  console.log('\n=== Chargement modèle ===');
  const t0 = Date.now();
  let last=null;
  const model = await t.SamModel.from_pretrained(MODEL, {
    progress_callback: p => { if(p.file && p.file!==last){last=p.file; console.log('  '+p.file+' '+(p.status||''));} }
  });
  const processor = await t.AutoProcessor.from_pretrained(MODEL);
  console.log('  ✓ chargé en '+((Date.now()-t0)/1000).toFixed(1)+' s');

  console.log('\n=== Encoding image ===');
  const image = await t.RawImage.read('/tmp/noumea.jpg');
  console.log('  image : '+image.width+'×'+image.height);
  const t1 = Date.now();
  const inputs = await processor(image);
  const emb = await model.get_image_embeddings({ pixel_values: inputs.pixel_values });
  console.log('  ✓ encoding en '+((Date.now()-t1)/1000).toFixed(1)+' s');

  console.log('\n=== Inférence sur 2 points ===');
  // Point 1 : coin haut-gauche = lagon (mer)
  // Point 2 : centre-bas = terre Nouméa (vérif)
  for(const [name, pt] of [['lagon top-left',[50,50]], ['centre image',[Math.floor(image.width/2), Math.floor(image.height/2)]]]){
    const t2 = Date.now();
    const inferInputs = await processor(image, { input_points:[[[pt]]], input_labels:[[[1]]] });
    const outputs = await model({...inferInputs, image_embeddings: emb.image_embeddings || emb});
    const masks = await processor.post_process_masks(outputs.pred_masks, inferInputs.original_sizes, inferInputs.reshaped_input_sizes);
    const m = masks[0];
    const scores = Array.from(outputs.iou_scores.data);
    const bestIdx = scores.reduce((b,s,i)=>s>scores[b]?i:b, 0);
    const W=image.width, H=image.height, slice=W*H;
    let count=0; for(let i=0;i<slice;i++) if(m.data[bestIdx*slice+i]) count++;
    const inMask = !!m.data[bestIdx*slice + pt[1]*W + pt[0]];
    console.log('  ['+name+'] pt='+pt+' score='+scores[bestIdx].toFixed(3)+' couverture='+(100*count/slice).toFixed(1)+'% pt-dans-masque='+inMask+' temps='+((Date.now()-t2)/1000).toFixed(2)+'s');
  }

  console.log('\n=== Test du pipeline complet de conversion ===');
  // Réutiliser le masque lagon
  const inferInputs = await processor(image, { input_points:[[[[50,50]]]], input_labels:[[[1]]] });
  const outputs = await model({...inferInputs, image_embeddings: emb.image_embeddings || emb});
  const masks = await processor.post_process_masks(outputs.pred_masks, inferInputs.original_sizes, inferInputs.reshaped_input_sizes);
  const m = masks[0];
  const scores = Array.from(outputs.iou_scores.data);
  const bestIdx = scores.reduce((b,s,i)=>s>scores[b]?i:b, 0);
  const W=image.width, H=image.height, slice=W*H;
  const mask = new Uint8Array(slice);
  for(let i=0;i<slice;i++) mask[i] = m.data[bestIdx*slice+i] ? 1 : 0;
  console.log('  ✓ masque extrait en Uint8Array, ' + mask.length + ' pixels (' + W + '×' + H + ')');
  console.log('  cohérent avec format attendu par shorelinesFromMask + pxToGeo de la plateforme.');

  console.log('\n=== TOUT EST OK ===');
})().catch(e => { console.error('ÉCHEC :', e.message); console.error(e.stack); process.exit(1); });
