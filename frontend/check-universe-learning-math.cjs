const ts=require('typescript'), fs=require('node:fs'), assert=require('node:assert/strict');
(async()=>{
  const code=ts.transpileModule(fs.readFileSync(`${__dirname}/src/pages/universe/learningMath.ts`,'utf8'),{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2020}}).outputText;
  const m=await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
  assert.deepEqual(m.unwrapLongitudes([358,1,3,359,357]),[358,361,363,359,357]);
  const labels=m.placeLabels([{id:'Earth',x:100,y:100},{id:'Moon',x:100,y:100},{id:'Sun',x:102,y:101}], 'Moon',300,300);
  assert.equal(labels.Moon.dy,0);
  assert.notEqual(labels.Earth.dy,labels.Moon.dy);
  assert.notEqual(labels.Sun.dy,labels.Earth.dy);
  assert.equal(m.speedExplanation(604800),'One second moves one week.');
  assert.equal(m.clampTime(-10,0,100),0);
  assert.equal(m.clampTime(110,0,100),100);
  assert.deepEqual(m.focusFrame([10,0,0],[0,0,0]).target,[5,0,0]);
  assert(m.focusFrame([10,0,0],[0,0,0]).distance>10);
  console.log('PASS: longitude wrap, selected-first collision avoidance, speed text, date clamp, paired focus');
})().catch(e=>{console.error(e);process.exit(1)});
