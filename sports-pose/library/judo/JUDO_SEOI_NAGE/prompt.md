# JUDO_SEOI_NAGE

Ippon seoi nage at the moment of lifting: tori turned in with the back against uke's chest, knees deeply bent with the hips below uke's hips, right upper arm locked under uke's right armpit, left hand pulling uke's right sleeve forward and down; uke bent over tori's back on the toes.

- 이름(ko): 유도 업어치기, 외깃 업어치기, 이폰 세오이나게, 업어치기 들어가기
- names (en): judo seoi nage, ippon seoi nage, shoulder throw, judo shoulder throw lift

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #JUDO_SEOI_NAGE

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 10 deg, turned 30 deg to the athlete's left of the chest line; face pointing down and to the athlete's left and slightly forward. Head turned to the left, eyes looking forward and down in the direction of the throw.
- Torso: trunk line (hips to shoulders) 40 deg forward of vertical; spine flexed 20 deg over the pelvis; shoulders square with the hips.
- Right arm (right arm locked under uke's armpit): upper arm raised 130 deg from the side of the trunk, pointing forward; elbow fully folded (145 deg flexion); forearm pointing backward and slightly up and slightly to the athlete's left; palm facing down; wrist flexed 33 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.19 m above the floor.
- Left arm (pulling hand on uke's sleeve): upper arm raised 52 deg from the side of the trunk, pointing down and slightly to the athlete's right; elbow fully folded (128 deg flexion); forearm pointing up and slightly forward; palm facing to the athlete's right and down and slightly backward; wrist flexed 30 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.15 m above the floor.
- Right leg: hip flexed 60 deg; knee bent to about a right angle (100 deg flexion); thigh pointing down and forward, shin pointing backward and slightly down; ankle dorsiflexed 34 deg; on the ball of the foot, heel raised.
- Left leg: hip flexed 60 deg; knee bent to about a right angle (100 deg flexion); thigh pointing down and forward, shin pointing backward and slightly down; ankle dorsiflexed 34 deg; on the ball of the foot, heel raised.
- Base: ankles 19 cm apart (11% of body height, 0.5x shoulder width); every support foot touches the floor, none floats.
- B (uke, being loaded onto tori's back): 25 cm backward of the main athlete, facing the main athlete; trunk 55 deg forward of vertical; knees 10/0 deg (right/left); elbows 75/35 deg; both feet on the floor. Uke in a blue judogi, pulled forward onto tori's back and up on the toes; uke's right arm drawn over tori's right shoulder, the forearm hanging in front of tori's chest.
- Technique cue: turn in with the hips below uke's
- Technique cue: pull the sleeve hand to your hip
- Technique cue: straighten the legs and bow forward to throw

3. OBJECT_INTERACTION:
- Legal under the IJF rules: tori's hands are on the jacket and sleeves, away from uke's legs; tori's head is well above the mat; no hand on the opponent's face.

4. CINEMATIC_CAMERA:
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view across the tatami, both judoka in profile.
- three_quarter: eye-level shot, three-quarter front view, 35mm standard lens, full-body shot. Three-quarter view, faces and grips sharp.
- high_cinema: overhead high-angle shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. High wide frame over the tatami, contest area colours and arena lights.

5. KINETIC_ENERGY:
- uke's feet about to leave the mat
- judogi jackets twisting and pulled open
- dust off the tatami
```

## Prompt (fill {SUBJECT}, {PARTNER_B} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a judoka loading the opponent onto the back for an ippon seoi nage. Opposite the main athlete: {PARTNER_B} as the uke, being loaded onto tori's back. Tori has turned in with the back against uke's chest, feet between uke's feet on the balls of the feet, knees deeply bent so the hips are below uke's; trunk bent forward; right arm bent with the upper arm locked up under uke's right armpit, the right hand gripping uke's upper sleeve; left hand pulling uke's right sleeve forward and down past the left hip; uke bent over tori's back, up on the toes. Turn in with the hips below uke's. Pull the sleeve hand to your hip. Straighten the legs and bow forward to throw. Eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view across the tatami, both judoka in profile. Uke's feet about to leave the mat; judogi jackets twisting and pulled open. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, judogi without a belt, both athletes in the same colour judogi, bare-chested judoka, boxing gloves, grabbing the legs, sleeves rolled up, tori standing upright with straight legs, tori's back not touching uke, hands grabbing the opponent's legs, thrower's head on the mat, hand pushing the opponent's face
```

## Control images

- `openpose_side.png` / `.json`: 1344x768, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_three_quarter.png` / `.json`: 1152x896, eye-level shot, three-quarter front view, 35mm standard lens, full-body shot.
- `openpose_high_cinema.png` / `.json`: 1344x768, overhead high-angle shot, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: B: r_arm.rot = 138 is beyond the usual range -70..120

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_knee_flex | 100.0 | 60..125 | knees deeply bent to drop the hips below uke's | KOD, EST |
| up:B.pelvis:pelvis | 24.9 | 10.. | tori's hips below uke's hips (the loading position) | KOD |
| r_elbow_flex | 145.0 | 80.. | right arm bent and locked under uke's armpit | KOD, EST |

## Official game rules (IJF Sport and Organisation Rules (SOR) and IJF Refereeing Rules)

| rule | what | check on this skeleton |
|---|---|---|
| IJF Refereeing Rules, prohibited acts | Grabbing the legs: Attacking or blocking with one or both hands or arms below the belt (grabbing the legs or trousers) is penalised. | OK: r palm 85 cm from B.r thigh mid |
| IJF Refereeing Rules, prohibited acts (hansoku-make) | Head diving: Diving head first into the tatami while throwing, bending forward and down, is hansoku-make; tori's head stays up off the mat. | OK: lowest of crown/forehead/nose +72 cm against a height of 0.40 m |
| IJF Refereeing Rules, prohibited acts | Hand on the face: Putting a hand, arm, foot or leg directly on the opponent's face is penalised. | OK: r palm 17 cm from B.nose |

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
