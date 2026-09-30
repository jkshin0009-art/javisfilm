# JUDO_IPPON_LANDING

The ippon moment after a throw: uke lands flat on the back with the chin tucked and the left arm slapping the mat (ukemi); tori stands over uke, still holding and pulling up uke's right sleeve.

- 이름(ko): 유도 한판, 유도 낙법 착지, 업어치기 한판, 메치기 착지
- names (en): judo ippon landing, judo throw landing, breakfall ukemi, ippon moment

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #JUDO_IPPON_LANDING

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 14 deg; face pointing down and slightly forward. Tori's eyes on uke.
- Torso: trunk line (hips to shoulders) 45 deg forward of vertical; spine flexed 25 deg over the pelvis; shoulders square with the hips.
- Right arm (right arm released): upper arm raised 35 deg from the side of the trunk, pointing down; elbow bent (60 deg flexion); forearm pointing forward and down; palm facing to the athlete's left and slightly down and slightly backward; wrist neutral; hand: relaxed, fingers softly curled; fingertips 0.62 m above the floor.
- Left arm (pulling hand still on uke's sleeve): upper arm raised 59 deg from the side of the trunk, pointing down and slightly to the athlete's right; elbow slightly bent (10 deg flexion); forearm pointing down and to the athlete's right; palm facing down and backward and slightly to the athlete's left; wrist extended (cocked back) 12 deg; hand: fingers wrapped firmly around what it holds; fingertips 0.65 m above the floor.
- Right leg: hip flexed 30 deg; knee bent (35 deg flexion); thigh pointing down, shin pointing down and slightly backward; ankle dorsiflexed 23 deg; foot flat on the floor.
- Left leg: hip flexed 24 deg; knee bent (30 deg flexion); thigh pointing down, shin pointing down and slightly backward; ankle dorsiflexed 24 deg; foot flat on the floor.
- Base: ankles 42 cm apart (24% of body height, 1.1x shoulder width); every support foot touches the floor, none floats.
- B (uke, landing on the back): 96 cm forward of the main athlete, with the back to the main athlete; trunk 90 deg backward of vertical; knees 60/40 deg (right/left); elbows 15/3 deg; lying with back upper, sacrum on the mat. Uke in a blue judogi landing flat on the back, chin tucked to the chest so the head does not hit the mat, left arm slapping the tatami at about 45 degrees from the body, legs up from the throw.
- Technique cue: keep pulling the sleeve so uke lands safely
- Technique cue: uke: chin to chest, slap the mat
- Technique cue: the referee raises the arm high for ippon

3. OBJECT_INTERACTION:
- Legal under the IJF rules: tori's hands are on the jacket and sleeves, away from uke's legs; tori's head is well above the mat; no hand on the opponent's face; uke's head stays off the mat (chin tucked).

4. CINEMATIC_CAMERA:
- side: high-angle shot looking down, side profile view, 35mm standard lens, full-body shot. Side view at mat level, tori standing over uke.
- high_three_quarter: overhead high-angle shot, three-quarter front view, 35mm standard lens, full-body shot. High three-quarter view of the landing, the referee's ippon signal behind.
- low_cinema: camera 0.3 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot. Low wide frame from the tatami, uke's slapping hand in the foreground.

5. KINETIC_ENERGY:
- tatami shock wave and dust at the impact
- judogi jackets flapping open
- referee's arm shooting up for ippon
```

## Prompt (fill {SUBJECT}, {PARTNER_B} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, the ippon moment: a judoka's opponent lands flat on the back after a throw. Opposite the main athlete: {PARTNER_B} as the uke, landing on the back. Tori stands over uke with knees bent and trunk leaning forward, the left hand still gripping the end of uke's right sleeve and pulling it up, the right arm released; uke lies flat on the back in front of tori's feet, chin tucked to the chest with the head off the mat, the left arm straight and slapping the tatami at about 45 degrees from the body, legs bent up from the throw. Keep pulling the sleeve so uke lands safely. Uke: chin to chest, slap the mat. The referee raises the arm high for ippon. High-angle shot looking down, side profile view, 35mm standard lens, full-body shot. Side view at mat level, tori standing over uke. Tatami shock wave and dust at the impact; judogi jackets flapping open. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, judogi without a belt, both athletes in the same colour judogi, bare-chested judoka, boxing gloves, grabbing the legs, sleeves rolled up, uke landing on the head, tori letting go of the sleeve, hands grabbing the opponent's legs, thrower's head on the mat, hand pushing the opponent's face, uke landing on the head or neck
```

## Control images

- `openpose_side.png` / `.json`: 1344x768, high-angle shot looking down, side profile view, 35mm standard lens, full-body shot.
- `openpose_high_three_quarter.png` / `.json`: 1344x768, overhead high-angle shot, three-quarter front view, 35mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.3 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| z:B.occiput | 0.1 | 0.04.. | uke's chin tucked: the back of the head does not hit the mat (ukemi) | KOD |
| z:B.l_palm | 0.0 | ..0.05 | uke's free arm slaps the mat | KOD |

## Official game rules (IJF Sport and Organisation Rules (SOR) and IJF Refereeing Rules)

| rule | what | check on this skeleton |
|---|---|---|
| IJF Refereeing Rules, prohibited acts | Grabbing the legs: Attacking or blocking with one or both hands or arms below the belt (grabbing the legs or trousers) is penalised. | OK: r palm 70 cm from B.r knee |
| IJF Refereeing Rules, prohibited acts (hansoku-make) | Head diving: Diving head first into the tatami while throwing, bending forward and down, is hansoku-make; tori's head stays up off the mat. | OK: lowest of crown/forehead/nose +85 cm against a height of 0.40 m |
| IJF Refereeing Rules, prohibited acts | Hand on the face: Putting a hand, arm, foot or leg directly on the opponent's face is penalised. | OK: l palm 56 cm from B.r eye |
| IJF Refereeing Rules, ippon | Ippon and safe landing: Ippon is a throw that lands the opponent largely on the back with speed, force and control; the thrower keeps hold of the sleeve so uke can break the fall, and uke tucks the chin and slaps the mat. | OK: lowest of B.occiput +5 cm against a height of 0.03 m |

Scene rules for a full match shot (players, uniforms, officials):

- One athlete in a white judogi, the other in a blue judogi; the jacket covers the thighs and closes left over right, sleeves reach the wrist, trousers reach the ankle; belt tied with a square knot; women wear a plain white T-shirt under the jacket, men nothing under it. (IJF SOR, judogi)
- No rings, watches, piercings or other hard objects; long hair tied back; nails cut short; barefoot on the tatami. (IJF SOR, hygiene)
- Square contest area 8-10 m across inside a 3 m safety area of a different colour; coach chairs at the corners. (IJF SOR, tatami)
- One referee on the mat; two judges at the table with the video replay (CARE) system; the referee raises one arm straight up for ippon. (IJF Refereeing Rules)

Rulebook: https://www.ijf.org/documents

## Sources

- [IJF] IJF Sport and Organisation Rules / Refereeing Rules: judogi, gripping, penalties (secondary summary of the SOR read this session; the IJF PDF itself not reachable) https://www.ijf.org/documents
- [KOD] Kodokan judo technique descriptions (kumikata, ippon seoi nage, kesa gatame) - general knowledge, not re-checked this session https://kodokanjudoinstitute.org/en/waza/
- [EST] Estimate from standard judo coaching (no measured joint angle checked this session) 
