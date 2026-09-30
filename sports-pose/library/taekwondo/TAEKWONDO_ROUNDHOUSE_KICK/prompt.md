# TAEKWONDO_ROUNDHOUSE_KICK

Taekwondo roundhouse kick (dollyeo chagi) to the trunk at impact: pivoting on the ball of the left foot with the heel toward the opponent, hips turned over, right leg snapped out with the instep on the opponent's trunk protector.

- 이름(ko): 태권도 돌려차기, 돌려차기 임팩트, 몸통 돌려차기, 반달차기
- names (en): taekwondo roundhouse kick, dollyeo chagi, turning kick to the body, roundhouse kick impact

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #TAEKWONDO_ROUNDHOUSE_KICK

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 36 deg, turned 36 deg to the athlete's right of the chest line; face pointing to the athlete's right and forward. Eyes on the target over the lead shoulder.
- Torso: trunk line (hips to shoulders) 13 deg backward of vertical, leaning 40 deg to the athlete's left; spine arched back (extended) 10 deg over the pelvis; shoulder line rotated 329 deg to the left of the hip line (hip-shoulder separation).
- Right arm (rear arm swinging down): upper arm raised 30 deg from the side of the trunk, pointing to the athlete's right and slightly down and slightly forward; elbow bent (40 deg flexion); forearm pointing forward and slightly to the athlete's right; palm facing down; wrist neutral; hand: closed fist; fingertips 1.24 m above the floor.
- Left arm (lead arm): upper arm raised 40 deg from the side of the trunk, pointing forward and slightly down and slightly to the athlete's right; elbow bent to about a right angle (100 deg flexion); forearm pointing up and slightly to the athlete's left and slightly forward; palm facing to the athlete's right and slightly up and slightly forward; wrist neutral; hand: closed fist; fingertips 1.43 m above the floor.
- Right leg (kicking leg): hip flexed 48 deg, abducted 63 deg; knee bent (37 deg flexion); thigh pointing to the athlete's right and slightly forward, shin pointing to the athlete's right and slightly backward; ankle plantar-flexed (toes pointed) 54 deg; foot 108 cm above the floor.
- Left leg (support leg): hip flexed 10 deg; knee slightly bent (15 deg flexion); thigh pointing down and slightly to the athlete's right, shin pointing down and to the athlete's right; ankle dorsiflexed 8 deg; on the ball of the foot, heel raised.
- Base: ankles 58 cm apart (32% of body height, 1.4x shoulder width); every support foot touches the floor, none floats.
- B (opponent in fighting stance): 110 cm to the athlete's right of the main athlete, turned side-on to the main athlete; trunk 10 deg forward of vertical; knees 12/20 deg (right/left); elbows 115/95 deg; both feet on the floor. Opponent in a closed fighting stance (left foot forward), guard up, electronic trunk protector on.
- Technique cue: pivot the support foot so the heel faces the target
- Technique cue: chamber the knee, then snap
- Technique cue: hit with the instep, toes pointed

3. OBJECT_INTERACTION:
- Legal under the WT rules: the kicking foot lands on the front or side of the trunk protector; the kicking foot is above the opponent's waist; neither fist is on the opponent's face.

4. CINEMATIC_CAMERA:
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view across the contest area, both athletes in profile.
- front_three_quarter: eye-level shot, three-quarter front view, 35mm standard lens, full-body shot. Three-quarter front view of the kicker, low and dynamic.
- low_cinema: camera 0.5 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot. Low wide frame from the mat, octagon edge and arena lights.

5. KINETIC_ENERGY:
- dobok trousers flaring with the kick
- sensor socks lighting the trunk protector on impact
- motion blur along the arc of the foot
```

## Prompt (fill {SUBJECT}, {PARTNER_B} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a taekwondo athlete landing a roundhouse kick on the opponent's trunk protector. Opposite the main athlete: {PARTNER_B} as the opponent in fighting stance. Balanced on the ball of the left foot, which has pivoted so the heel points at the opponent; hips turned over sideways; right leg raised to the side at trunk height with the knee snapping straight, instep and top of the foot striking the side of the opponent's trunk protector; body leaning back and away for balance; right arm swinging down beside the hip, left fist guarding the chest. Pivot the support foot so the heel faces the target. Chamber the knee, then snap. Hit with the instep, toes pointed. Eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view across the contest area, both athletes in profile. Dobok trousers flaring with the kick; sensor socks lighting the trunk protector on impact. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, black belt missing, trunk protector missing, kicking with the shin instead of the foot, bare chest, boxing gloves, southpaw stance, support foot pointing at the opponent, kicking with the toes, kick landing with the shin, kick to the opponent's spine, kick to the opponent's leg or knee, punch to the opponent's face, hand grabbing the opponent's dobok, catching the opponent's kicking leg, knee strike, head butt
```

## Control images

- `openpose_side.png` / `.json`: 1344x768, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_front_three_quarter.png` / `.json`: 1152x896, eye-level shot, three-quarter front view, 35mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.5 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: r_leg.abd = 63 is beyond the usual range -25..50

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_knee_flex | 36.8 | ..45 | kicking knee nearly extended at impact (snap) | KUK, EST |
| z:r_ankle | 1.1 | 0.8..1.4 | kick lands on the trunk protector (from the belt to the armpits) | WT |

## Official game rules (World Taekwondo Competition Rules & Interpretation (Olympic sparring, kyorugi))

| rule | what | check on this skeleton |
|---|---|---|
| WT Permitted techniques and areas | Kick lands with the foot on the trunk protector: A kick scores only when the part of the foot below the ankle bone lands on a permitted area; the trunk protector may be attacked by fist and foot, but not the spine. | OK: r instep 0 cm from B.belly |
| WT Prohibited acts (gam-jeom): attacking below the waist | Attacking below the waist: Kicking or attacking the opponent below the waist is a gam-jeom (penalty point to the opponent). | OK: lowest of r_ankle +18 cm against the B.belt front |
| WT Prohibited acts (gam-jeom): hitting the head with the hand | Hand attack to the face: Hitting the opponent's head or face with the hand is a gam-jeom; the head may be attacked only by kicks. | OK: r knuckles 66 cm from B.nose |
| WT Prohibited acts (gam-jeom): grabbing, holding, pushing | Grabbing or pushing: Grabbing or holding the opponent or the opponent's leg or dobok, and pushing the opponent with the hands or body, are gam-jeom. | text only |
| WT Prohibited acts (gam-jeom): knee and head attacks | Kneeing or head butting: Attacking with the knee or butting with the head is a gam-jeom. | text only |

Scene rules for a full match shot (players, uniforms, officials):

- White dobok with a belt; electronic trunk protector and headgear in the athlete's colour, red (hong) or blue (chung); forearm and shin guards, gloves, sensor socks, groin guard and mouthguard, all worn under or over the dobok as the rules require. (WT Uniform and protective equipment)
- Flat, non-slip mat; the contest area is marked as an octagon (Olympic events) or a square, with a boundary line. (WT Competition area)
- One referee on the mat in a uniform; judges and a video-replay jury off the mat; coaches seated at the corners. (WT Officials)
- Punches with the knuckles of a tightly clenched fist, only to the trunk protector; kicks with the foot below the ankle bone, to the trunk protector or to the head above the collar bone. (WT Permitted techniques)

Rulebook: https://www.worldtaekwondo.org/rules-wt/rules.html

## Sources

- [WT] World Taekwondo Competition Rules & Interpretation: permitted techniques (knuckles of a clenched fist; foot below the ankle bone), permitted areas (trunk protector; head above the collar bone by foot only) - general knowledge, not re-checked this session https://www.worldtaekwondo.org/rules-wt/rules.html
- [KUK] Kukkiwon Taekwondo Textbook: fighting stance (gyeorugi junbi), dollyeo chagi and dwit chagi descriptions - general knowledge, not re-checked this session https://www.kukkiwon.or.kr
- [EST] Estimate from standard taekwondo coaching (no measured joint angle checked this session) 
