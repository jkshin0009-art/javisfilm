# JUDO_KUMIKATA

Two judoka in the standard right-handed grip (ai-yotsu): each right hand on the partner's left lapel at collarbone height, each left hand on the partner's right sleeve at the elbow, upright natural posture with the right foot slightly forward.

- 이름(ko): 유도 맞잡기, 유도 기본 잡기, 쿠미카타, 깃잡기 소매잡기
- names (en): judo grip, kumikata, judo standard grip, lapel and sleeve grip

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #JUDO_KUMIKATA

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 8 deg; face pointing forward and slightly down. Eyes on the partner's chest and shoulders.
- Torso: trunk line (hips to shoulders) 10 deg forward of vertical; spine flexed 5 deg over the pelvis; shoulders square with the hips.
- Right arm (lapel hand (tsurite)): upper arm raised 68 deg from the side of the trunk, pointing forward and slightly down and slightly to the athlete's right; elbow bent to about a right angle (92 deg flexion); forearm pointing to the athlete's left and forward; palm facing forward and slightly down; wrist extended (cocked back) 9 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.37 m above the floor.
- Left arm (sleeve hand (hikite)): upper arm raised 46 deg from the side of the trunk, pointing down and to the athlete's left; elbow fully folded (110 deg flexion); forearm pointing forward and slightly to the athlete's right; palm facing down and forward; wrist extended (cocked back) 25 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.29 m above the floor.
- Right leg: hip flexed 14 deg; knee slightly bent (18 deg flexion); thigh pointing down, shin pointing down; ankle dorsiflexed 8 deg; foot flat on the floor.
- Left leg: hip flexed 1 deg; knee slightly bent (8 deg flexion); thigh pointing down, shin pointing down; ankle dorsiflexed 11 deg; foot flat on the floor.
- Base: ankles 37 cm apart (21% of body height, 0.9x shoulder width); every support foot touches the floor, none floats.
- B (partner (uke) in the same right-handed grip): 72 cm forward of the main athlete, facing the main athlete; trunk 10 deg forward of vertical; knees 18/8 deg (right/left); elbows 90/121 deg; both feet on the floor. Partner in a blue judogi, mirror-image grip: right hand on the left lapel, left hand on the right sleeve.
- Technique cue: grip with the little and ring fingers
- Technique cue: keep the posture upright (shizentai)
- Technique cue: elbows down, not flared

3. OBJECT_INTERACTION:
- Legal under the IJF rules: tori's hands are on the jacket and sleeves, away from uke's legs; no hand on the opponent's face.

4. CINEMATIC_CAMERA:
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view across the tatami, both judoka in profile.
- three_quarter: eye-level shot, three-quarter front view, 35mm standard lens, full-body shot. Three-quarter view, faces and grips sharp.
- high_cinema: overhead high-angle shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. High wide frame over the tatami, contest area colours and arena lights.

5. KINETIC_ENERGY:
- judogi fabric pulled taut at the collar
- belts and jacket skirts swinging
- tatami squeaking under the feet
```

## Prompt (fill {SUBJECT}, {PARTNER_B} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, two judoka gripping each other in the standard right-handed grip. Opposite the main athlete: {PARTNER_B} as the partner (uke) in the same right-handed grip. Both standing upright in a natural posture, feet about shoulder width apart, knees soft, right foot slightly forward; each right hand grips the partner's left lapel at collarbone height with the knuckles up; each left hand grips the partner's right sleeve just below the elbow; elbows down, arms bent. Grip with the little and ring fingers. Keep the posture upright (shizentai). Elbows down, not flared. Eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view across the tatami, both judoka in profile. Judogi fabric pulled taut at the collar; belts and jacket skirts swinging. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, judogi without a belt, both athletes in the same colour judogi, bare-chested judoka, boxing gloves, grabbing the legs, sleeves rolled up, grip on the belt, hands on the partner's neck, hands grabbing the opponent's legs, fingers inside the opponent's sleeve, hand pushing the opponent's face, judoka bent over at the waist to defend
```

## Control images

- `openpose_side.png` / `.json`: 1344x768, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_three_quarter.png` / `.json`: 1152x896, eye-level shot, three-quarter front view, 35mm standard lens, full-body shot.
- `openpose_high_cinema.png` / `.json`: 1344x768, overhead high-angle shot, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_elbow_flex | 91.5 | 30..130 | lapel arm bent, fist at the partner's collarbone | KOD, EST |
| trunk_lean_fwd | 10.0 | ..20 | upright natural posture (shizentai), not bent over | IJF |
| stance_over_shoulders | 0.9 | 0.8..1.6 | feet about shoulder width apart | KOD, EST |

## Official game rules (IJF Sport and Organisation Rules (SOR) and IJF Refereeing Rules)

| rule | what | check on this skeleton |
|---|---|---|
| IJF Refereeing Rules, prohibited acts | Grabbing the legs: Attacking or blocking with one or both hands or arms below the belt (grabbing the legs or trousers) is penalised. | OK: l palm 61 cm from B.r thigh mid |
| IJF Refereeing Rules, gripping | Non-standard grips: A cross grip, a one-sided grip, a belt grip or a grip on the back must be followed by an attack within a few seconds; fingers inside the opponent's sleeve or trouser leg, and the pistol grip on the sleeve end, are penalised. | text only |
| IJF Refereeing Rules, prohibited acts | Hand on the face: Putting a hand, arm, foot or leg directly on the opponent's face is penalised. | OK: r palm 20 cm from B.chin |
| IJF Refereeing Rules, prohibited acts (shido) | Defensive posture: Bending over excessively to avoid being thrown, or holding without attacking, is penalised with shido. | text only |

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
