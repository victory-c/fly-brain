// bike_livery.js: the Colnago V4Rs's looks, shared by export_attempts (/ride/) and export_ride3d (/ride/3d) and inlined into both pages.
// Needs three.js r128 + examples/js/geometries/DecalGeometry.js, and the page's V(x,y,z), Z = V(0,0,1) and renderer. The page rigs the GLB, then
// calls liveryRig(m, root) once (m: the GLTF scene, root: the rig everything was reparented under) and liveryApply(value, scope) on every change.
// LIVERIES: [value (?paint=), label key, frame colour, decal kinds, logo colour, frame roughness]. UAE white carries 'SHIMANO UAE | Emirates' on the
// chainstays; Pogačar rainbow is the same white bike with the UCI world-champion bands (seat tube, fork, head tube, a mark by each rim logo);
// carbon black is Pogačar's black team bike: satin carbon, white COLNAGO, red lower fork legs with 'UAE' / 'Emirates', his name on the seat stay.
// Every livery runs Continental Grand Prix 5000 TT tyres on ENVE SES 4.5 rims: the model ships Pirelli P Zero on Campagnolo Bora, both repainted.
const LIVERIES=[['orig','pOrig'],['f2f2f2','pUAE','f2f2f2',['uae']],['rainbow','pRainbow','f2f2f2',['uae','rainbow']],['c8102e','pRed','c8102e'],
 ['16181c','pCarbon','16181c',['carbon'],'ececec',0.5]];
const LIV={paints:[],logos:[],decals:[],rims:[]};
// the sidewall / rim lettering faces, from jsDelivr: Michroma (wide square, slanted for GRAND PRIX, heavy for ENVE), Bitter ExtraBold (Continental);
// the textures are drawn at once with fallbacks and redrawn when these arrive
const LIV_FONTS=(()=>{try{return Promise.all([['LivMichroma','michroma@5/files/michroma-latin-400-normal.woff2','400'],['LivBitter','bitter@5/files/bitter-latin-800-normal.woff2','800']]
 .map(([n,p,w])=>new FontFace(n,'url(https://cdn.jsdelivr.net/npm/@fontsource/'+p+')',{weight:w}).load().then(f=>document.fonts.add(f)))).catch(e=>console.warn('livery fonts',e))}
 catch(e){return Promise.resolve()}})();
const MICHROMA='LivMichroma,"Eurostile","Helvetica Neue",Arial,sans-serif';
function liveryRig(m,root){
 root.traverse(o=>{if(!o.isMesh||!o.material)return;const mt=o.material,u=mt.userData;
  if(mt.name==='RVBU'&&!LIV.paints.includes(mt)){u.paint=true;u.orig=mt.color.getHex();u.rough=mt.roughness;LIV.paints.push(mt)}
  if(mt.name==='RVBU logo'&&!LIV.logos.includes(mt)){u.orig=mt.color.getHex();u.map=mt.map;u.metal=mt.metalness;u.rough=mt.roughness;LIV.logos.push(mt)}});
 root.updateMatrixWorld(true);addLivery(m,n=>root.getObjectByName(THREE.PropertyBinding.sanitizeNodeName(n)));  // by root: the fork hangs under the steering
 tyresGP5000(root);rimsENVE(root)}
// paint every userData.paint material under scope (the GLB frame, or a procedural bike: list = that bike's own colours), and switch the extras
function liveryApply(v,scope,list=LIVERIES){const p=list.find(x=>x[0]===v)||list[0],hex=p[2],kinds=p[3]||[];
 scope.traverse(o=>{if(o.isMesh&&o.material&&o.material.userData.paint){const m=o.material;if(!hex){if(m.userData.orig!==undefined)m.color.setHex(m.userData.orig)}else m.color.setHex(parseInt(hex,16)).convertSRGBToLinear();
  if(m.userData.rough!==undefined)m.roughness=p[5]!==undefined?p[5]:m.userData.rough}});
 for(const m of LIV.logos){const u=m.userData;if(p[4]){m.map=null;m.metalness=0;m.roughness=0.45;m.color.setHex(parseInt(p[4],16)).convertSRGBToLinear()}  // fully metallic: with no env map it renders black
  else{m.map=u.map;m.metalness=u.metal;m.roughness=u.rough;m.color.setHex(u.orig)}m.needsUpdate=true}
 for(const d of LIV.decals)d.visible=kinds.includes(d.userData.kind);
 for(const r of LIV.rims)r.mat.map=kinds.includes('rainbow')?r.rainbow:r.plain}
// livery decals, after Pogačar's world-champion V4Rs: 'SHIMANO UAE | Emirates' on both chainstays; the rainbow bands (slanted, blue on top) on the seat tube
// under the seat-stay junction and on the fork legs under the crown, plus a thin rainbow mark at the top of the head tube; the top tube stays clean.
// Projected onto the frame and fork with DecalGeometry and parented to the mesh they sit on, so the fork's follow the steering. Placements are in
// the GLB's own space, read off the mesh: seat-tube centre x = -0.1685 - 0.309 (y - 0.50) (36 mm), fork-leg centre x = 0.3882 - 0.446 (y - 0.58)
// at z = ±0.04 (40 mm), chainstay centre (-0.305, 0.303, ±0.046) running (1, -0.183, ∓0.163) (30-35 mm tall), head tube 18° off vertical.
const RAINBOW=['#009a44','#ffd100','#111111','#e4002b','#0072ce'];  // UCI bands from the bottom up: green, yellow, black, red, blue
function canvasTex(w,h,draw){const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);
 const t=new THREE.CanvasTexture(c);t.encoding=THREE.sRGBEncoding;t.anisotropy=renderer.capabilities.getMaxAnisotropy();return t}
// bands across a tube: L long in total, the decal W wide; each band boundary runs u = u0 + k v, so the bands lean like the painted ones
function bandsTex(L,W,k){const X=L+Math.abs(k)*W;return [X,canvasTex(512,128,(x,w,h)=>{const pu=u=>(u/X+0.5)*w,pv=v=>(0.5-v/W)*h;
 RAINBOW.forEach((c,i)=>{const a=-L/2+i*L/5,b=a+L/5+0.0005;x.fillStyle=c;x.beginPath();
  x.moveTo(pu(a-k*W/2),pv(-W/2));x.lineTo(pu(b-k*W/2),pv(-W/2));x.lineTo(pu(b+k*W/2),pv(W/2));x.lineTo(pu(a+k*W/2),pv(W/2));x.fill()})})]}
function stripesTex(){return canvasTex(8,160,(x,w,h)=>RAINBOW.forEach((c,i)=>{x.fillStyle=c;x.fillRect(0,i*h/5,w,h/5+1)}))}  // along the tube, blue at v = 0
function uaeTex(){return canvasTex(1024,126,(x,w,h)=>{const F0='italic 800 80px "Helvetica Neue",Arial,sans-serif',F1='700 84px "Helvetica Neue",Arial,sans-serif',F2='400 80px Georgia,"Times New Roman",serif';
 x.font=F0;const z=x.measureText('SHIMANO').width;x.font=F1;const a=x.measureText('UAE').width;x.font=F2;const b=x.measureText('Emirates').width;
 const sp=46,gap=26,bar=5,tot=z+sp+a+2*gap+bar+b,s=Math.min(1,(w-24)/tot);
 x.translate(w/2,h/2);x.scale(s,s);x.translate(-tot/2,0);x.fillStyle='#111';x.textBaseline='middle';x.font=F0;x.fillText('SHIMANO',0,5);x.translate(z+sp,0);
 x.font=F1;x.fillText('UAE',0,5);x.fillRect(a+gap,-40,bar,84);x.font=F2;x.fillText('Emirates',a+2*gap+bar,3)})}
function addLivery(m,by){if(!THREE.DecalGeometry)return;
 const pick=n=>{let r=null;const o=by(n);if(o)o.traverse(c=>{if(!r&&c.isMesh)r=c});return r};
 const frame=pick('V4_510_SDM3_Frame004_RVBU'),fork=pick('V4_510_SDM3_Fork004_RVBU');
 // the decal's u runs along `axis`, its projection along `out` (through the whole tube for the bands, outer half only for the lettering)
 const put=(mesh,kind,tex,at,axis,out,size,layer=0)=>{if(!mesh)return;if(!mesh.geometry.attributes.normal)mesh.geometry.computeVertexNormals();
  const ex=axis.clone().normalize(),ez=out.clone().addScaledVector(ex,-out.dot(ex)).normalize(),ey=new THREE.Vector3().crossVectors(ez,ex);
  const q=new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(ex,ey,ez));
  const d=new THREE.DecalGeometry(mesh,m.localToWorld(at.clone()),new THREE.Euler().setFromQuaternion(q),size);if(!d.attributes.position.count)return;
  d.applyMatrix4(new THREE.Matrix4().copy(mesh.matrixWorld).invert());
  const o=new THREE.Mesh(d,new THREE.MeshStandardMaterial({map:tex,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-4-4*layer,polygonOffsetUnits:-4-4*layer,
   roughness:mesh.material.roughness,metalness:mesh.material.metalness}));
  o.userData.kind=kind;o.renderOrder=layer;o.receiveShadow=mesh.receiveShadow;o.visible=false;mesh.add(o);LIV.decals.push(o)};
 const ang=a=>V(Math.cos(a),Math.sin(a)),lean=(axis,phi)=>{const n=axis.clone().normalize(),v=V(-n.y,n.x),d=ang(phi);return d.dot(n)/d.dot(v)};  // band slope k
 const seat=V(-0.309,1),fk=V(-0.446,1),head=V(-Math.sin(18*Math.PI/180),Math.cos(18*Math.PI/180)),PHI=-22*Math.PI/180;  // band edges 22° below horizontal, dropping to the front
 const [sx,st]=bandsTex(0.09,0.046,lean(seat,PHI)),[fx,ft]=bandsTex(0.08,0.05,lean(fk,PHI));
 put(frame,'rainbow',st,V(-0.170,0.505,0),seat,Z,V(sx,0.046,0.12));
 put(fork,'rainbow',ft,V(0.386,0.585,0),fk,Z,V(fx,0.05,0.2));
 put(frame,'rainbow',stripesTex(),V(0.322,0.758,0),head,Z,V(0.032,0.011,0.12));
 const uae=uaeTex();for(const s of[1,-1]){const ax=V(1,-0.183,-0.163*s),out=V(0.163,0,s);   // one per chainstay, outer half only, reading left to right from that side
  put(frame,'uae',uae,V(-0.31,0.3035,0.046*s).addScaledVector(out.clone().normalize(),0.02),s>0?ax:ax.negate(),out,V(0.21,0.026,0.04))}
 // carbon black: the fork legs red from the dropouts up to a slanted cut, 'UAE' in white above it and 'Emirates' in white on it, reading down the leg
 // on both sides (leg centre z = 0.0385 + 0.069 (0.60 - y), the legs splay out toward the dropouts); 'POGAČAR' with the Slovenian flag on the
 // drive-side seat stay, reading up toward the seat tube (stay centre (-0.355, 0.5305, 0.0475) running (1, 1.144, -0.219), 16 mm thick)
 const legX=y=>0.3882-0.446*(y-0.58),legZ=y=>0.0385+0.069*(0.60-y),[rx,rt]=redTex(0.2,0.07,lean(fk,-12*Math.PI/180));
 put(fork,'carbon',rt,V(legX(0.415),0.415,0),fk,Z,V(rx,0.07,0.2));
 const tU=wordTex('UAE','700 {}px "Helvetica Neue",Arial,sans-serif',0.05,0.026),tE=wordTex('Emirates','400 {}px Georgia,"Times New Roman",serif',0.13,0.03);
 for(const s of[1,-1]){const out=V(0,0,s),down=V(0.446,-1,0.069*s),at=y=>V(legX(y),y,legZ(y)*s).addScaledVector(out,0.02);
  put(fork,'carbon',tU,at(0.555),down,out,V(0.05,0.026,0.04),1);put(fork,'carbon',tE,at(0.43),down,out,V(0.13,0.03,0.04),1)}
 put(frame,'carbon',nameTex(),V(-0.355,0.5305,0.0675),V(1,1.144,-0.219),V(0,0.35,1),V(0.085,0.017,0.04),1)}
// a red block along the tube: L long, its top end cut on the slant like the bands; W wide
function redTex(L,W,k){const X=L+Math.abs(k)*W;return [X,canvasTex(512,128,(x,w,h)=>{const pu=u=>(u/X+0.5)*w,pv=v=>(0.5-v/W)*h;
 x.fillStyle='#d8141e';x.beginPath();x.moveTo(0,pv(-W/2));x.lineTo(pu(L/2-k*W/2),pv(-W/2));x.lineTo(pu(L/2+k*W/2),pv(W/2));x.lineTo(0,pv(W/2));x.fill()})]}
// white lettering filling an X by Y decal ({} in the font takes the size)
function wordTex(txt,font,X,Y){const w=1024,h=Math.round(w*Y/X);return canvasTex(w,h,(x)=>{let f=Math.round(h*0.78);x.font=font.replace('{}',f);
 const tw=x.measureText(txt).width;if(tw>w*0.94){f=Math.floor(f*w*0.94/tw);x.font=font.replace('{}',f)}
 x.fillStyle='#f4f4f4';x.textAlign='center';x.textBaseline='middle';x.fillText(txt,w/2,h/2+f*0.05)})}
function nameTex(){return canvasTex(1024,205,(x,w,h)=>{const fh=110,fw=165,F='800 128px "Helvetica Neue",Arial,sans-serif';x.font=F;const tw=x.measureText('POGAČAR').width,gap=34,tot=fw+gap+tw;
 x.translate((w-tot)/2,h/2);['#ffffff','#0047ab','#e4002b'].forEach((c,i)=>{x.fillStyle=c;x.fillRect(0,-fh/2+i*fh/3,fw,fh/3+0.5)});  // Slovenia: white / blue / red,
 x.fillStyle='#0047ab';x.beginPath();x.moveTo(fw*0.2,-fh/2+fh*0.12);x.lineTo(fw*0.44,-fh/2+fh*0.12);x.lineTo(fw*0.44,fh*0.06);x.quadraticCurveTo(fw*0.32,fh*0.2,fw*0.2,fh*0.06);x.closePath();x.fill();  // the arms
 x.strokeStyle='#e4002b';x.lineWidth=5;x.stroke();x.fillStyle='#fff';x.beginPath();x.moveTo(fw*0.22,0);x.lineTo(fw*0.32,-fh*0.22);x.lineTo(fw*0.42,0);x.fill();
 x.fillStyle='#f4f4f4';x.font=F;x.textBaseline='middle';x.fillText('POGAČAR',fw+gap,6)})}
// a canvas texture standing in for a GLB one (same wrap / flip / encoding), drawn now and again once the lettering fonts are in
function liveTex(tex,draw){const c=document.createElement('canvas');c.width=c.height=2048;const x=c.getContext('2d'),t=tex.clone();t.image=c;
 const go=()=>{x.setTransform(2,0,0,2,0,0);x.clearRect(0,0,1024,1024);draw(x);t.needsUpdate=true};go();LIV_FONTS.then(go);return t}
// tyres: Continental Grand Prix 5000 TT for the model's Pirelli P Zero Race TLR. The sidewall texture ('Material #358', 1024²) is a disc whose ring
// r 477-502 px is the visible sidewall (16 mm, rim to tread); the P Zero lettering sits on it ±16° about the top and the bottom, tops outward.
// Repaint ±27° of that ring as on the real tyre: 'Continental' and the horse, then wide slanted GRAND PRIX 5000 TT; flatten the same ring in the
// normal map so the embossed P ZERO goes too. Both wheels share the texture.
function tyresGP5000(root){const done=new Map(),SPAN=[[-117,-63],[63,117]].map(s=>s.map(a=>a*Math.PI/180));
 const ring=(x,fill)=>{x.fillStyle=fill;for(const [a,b] of SPAN){x.beginPath();x.arc(512,512,504,a,b);x.arc(512,512,476,b,a,true);x.closePath();x.fill()}};
 const runs=[{t:'Continental',f:'800 10px LivBitter,Georgia,serif',g:1.5,dy:0.5},{draw:horse,w:8,g:9},
  {t:'GRAND PRIX 5000 TT',f:'14.5px '+MICHROMA,sx:1.05,skew:-0.3,stroke:0.9}];
 const redo=(tex,fill,letters)=>{if(!tex||!tex.image)return tex;if(!done.has(tex))done.set(tex,liveTex(tex,x=>{x.drawImage(tex.image,0,0,1024,1024);ring(x,fill);
  if(letters)for(const mid of[-Math.PI/2,Math.PI/2])arcText(x,mid,489.5,runs,'#e8e8e8')}));return done.get(tex)};
 root.traverse(o=>{if(o.isMesh&&o.material&&o.material.name==='Material #358'){const m=o.material;m.map=redo(m.map,'#0a0a0a',true);m.normalMap=redo(m.normalMap,'rgb(128,128,255)',false);m.needsUpdate=true}})}
// rims: ENVE SES 4.5 for the model's Campagnolo Bora Ultra WTO 45. The rim texture ('Wheel Rim Bora WTO', 1024²) is brushed carbon in horizontal
// streaks mapped as a disc, the rim face (45 mm) on r 439-512 px; BORA ULTRA WTO 45 runs over the top (rows 25-160), the Campagnolo mark sits at the
// bottom (rows 955-1020). Cover both with clean streaks from mid-texture, then three big white ENVE logos 120° apart with 'SES 4.5' after each
// (and a little rainbow flag on the Pogačar rainbow bike, so each rim gets a plain and a rainbow texture, swapped by liveryApply).
function rimsENVE(root){const done=new Map();
 const clean=(x,img)=>{x.drawImage(img,0,0,1024,1024);x.drawImage(img,0,300,1024,180,0,0,1024,180);x.drawImage(img,0,600,1024,110,0,914,1024,110)};
 const logos=(x,flag)=>{for(const mid of[-90,30,150])arcText(x,mid*Math.PI/180,476,[{t:'ENVE',f:'64px '+MICHROMA,sx:1.25,stroke:7,g:30,dy:2},
  {t:'SES 4.5',f:'15px '+MICHROMA,stroke:0.6,g:flag?14:0,dy:1},...(flag?[{draw:rainbowFlag,w:20}]:[])],'#f2f2f2')};
 root.traverse(o=>{if(!o.isMesh||!o.material||o.material.name!=='Wheel Rim Bora WTO')return;const m=o.material,tex=m.map;if(!tex||!tex.image)return;
  if(!done.has(tex))done.set(tex,{plain:liveTex(tex,x=>{clean(x,tex.image);logos(x,false)}),rainbow:liveTex(tex,x=>{clean(x,tex.image);logos(x,true)})});
  const d=done.get(tex);if(!LIV.rims.some(r=>r.mat===m))LIV.rims.push({mat:m,plain:d.plain,rainbow:d.rainbow});m.map=d.plain;
  if(m.normalMap&&m.normalMap.image&&!done.has(m.normalMap)){const n=m.normalMap;done.set(n,liveTex(n,x=>clean(x,n.image)))}if(m.normalMap)m.normalMap=done.get(m.normalMap);m.needsUpdate=true})}
// lettering along a circle about (512, 512) of radius r, centred on angle mid (canvas angles, clockwise), tops outward. Runs:
// {t, f font, g gap after, sx x stretch, skew (negative leans the tops forward), stroke width, dy sink} or {draw(x) in a box w wide, w, g}
function arcText(x,mid,r,runs,col){let tot=0;for(const q of runs){if(q.draw)tot+=q.w+(q.g||0);else{x.font=q.f;tot+=x.measureText(q.t).width*(q.sx||1)+(q.g||0)}}
 let a=mid-tot/(2*r);x.fillStyle=x.strokeStyle=col;x.textBaseline='middle';x.textAlign='center';x.lineJoin='round';
 const at=(w,fn)=>{a+=w/(2*r);x.save();x.translate(512+r*Math.cos(a),512+r*Math.sin(a));x.rotate(a+Math.PI/2);fn();x.restore();a+=w/(2*r)};
 for(const q of runs){if(q.draw)at(q.w,()=>q.draw(x));
  else{x.font=q.f;x.lineWidth=q.stroke||0;for(const ch of q.t)at(x.measureText(ch).width*(q.sx||1),()=>{x.transform(q.sx||1,0,q.skew||0,1,0,0);x.fillText(ch,0,q.dy||0);if(q.stroke)x.strokeText(ch,0,q.dy||0)})}
  a+=(q.g||0)/r}}
function horse(x){x.beginPath();  // the Continental horse, rearing to the right, ~8 px
 [[-3.6,4],[-3,0.8],[-1.4,-0.4],[0.2,-2.2],[1.2,-4.2],[2.6,-4.6],[3.8,-3.6],[2.8,-2.8],[3.6,-1.2],[2.6,-0.6],[1.8,-1.6],[1.2,0.2],[1.6,2],[0.8,4],[0.2,4],[0.4,2],[-0.8,1.6],[-1.6,4]]
  .forEach(([px,py],i)=>i?x.lineTo(px,py):x.moveTo(px,py));x.closePath();x.fill()}
function rainbowFlag(x){RAINBOW.slice().reverse().forEach((c,i)=>{x.fillStyle=c;x.fillRect(-9,-8+i*3.2,18,3.3)})}  // blue outward
