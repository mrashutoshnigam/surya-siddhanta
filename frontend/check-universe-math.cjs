// No new test runtime: compile the pure TypeScript module in memory.
const ts = require('typescript');
const fs = require('node:fs');
const assert = require('node:assert/strict');
(async () => {
  const code = ts.transpileModule(fs.readFileSync(`${__dirname}/src/pages/universe/math.ts`, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const math = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
  const a={timestamp:0,positions:{Earth:[0,0,0],Moon:[1,0,0]},velocities:{Earth:[0,0,0],Moon:[0,1,0]}};
  const b={timestamp:86400,positions:{Earth:[0,0,0],Moon:[0,1,0]},velocities:{Earth:[0,0,0],Moon:[-1,0,0]}};
  assert.deepEqual(math.sampleAt([a,b],0).Moon,[1,0,0]);
  assert.deepEqual(math.sampleAt([a,b],86400).Moon,[0,1,0]);
  assert.deepEqual(math.sampleAt([a,b],43200).Moon,[.625,.625,0]);
  assert.equal(math.sampleAt([a,b],-1),null);
  assert.equal(math.sampleAt([a,b],86401),null);
  assert.equal(math.parseClock('2026-11-06T12:00',5.5), Date.parse('2026-11-06T06:30Z')/1000);
  assert.equal(math.formatClock(Date.parse('2026-11-06T06:30Z')/1000,5.5),'2026-11-06T12:00');
  assert.equal(math.parseClock('2024-02-30T12:00',0),null);
  assert.equal(math.parseClock('1500-01-01T12:00',0),null);
  const points={Sun:[0,0,0],Earth:[1,0,0],Moon:[1,.00257,0]};
  const earth=math.scenePosition('Earth',points,'modern'), moon=math.scenePosition('Moon',points,'modern');
  assert(Math.hypot(...earth)>2);
  assert(Math.hypot(...moon.map((v,i)=>v-earth[i]))>1);
  assert.deepEqual(math.scenePosition('Earth',{Earth:[0,0,0]},'historical'),[0,0,0]);
  assert.equal(math.angularDifference(359,1),2);
  assert.equal(math.angularDifference(1,359),-2);
  console.log('PASS: Hermite interpolation, bounds, UTC offsets, calendar validation, lunar separation, angle wrap');
})().catch(error=>{console.error(error);process.exit(1)});
