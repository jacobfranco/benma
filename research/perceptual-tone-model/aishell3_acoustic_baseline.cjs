// Pure acoustic bridge to frozen production functions. No expected tone or text.
const fs=require('node:fs');
const {load}=require('../../benchmark/pronunciation_v2/tone_feedback.cjs');
const {verifyBaseline}=require('./evaluate.cjs');
function classify(row) {
  const {unitShape}=load('@/speech/pitchShapeEvidence');
  const {classifyToneLikeness}=load('@/speech/toneLikeness');
  const unit={start:row.start,end:row.end,grouped:false};
  const shape=unitShape({tone_graph:{raw:row.raw}},unit,row.segments);
  const observed=classifyToneLikeness(shape,row.segments);
  return {example_id:row.example_id,prediction:observed.decision==='NUMBERED'?observed.tone.replace('TONE_','T'):null,
    shape,observed,eligibility:row.eligibility,segments:row.segments,duration:row.end-row.start};
}
module.exports={classify};
if(require.main===module){
  verifyBaseline();
  const [input,output]=process.argv.slice(2);
  fs.writeFileSync(output,JSON.stringify(JSON.parse(fs.readFileSync(input)).map(classify))+'\n',{flag:'wx'});
}
