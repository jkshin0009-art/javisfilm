# TAEKWONDO_BACK_KICK

Taekwondo back kick (dwit chagi) at impact: back turned to the opponent, looking over the right shoulder, right leg thrust straight back with the heel and sole on the opponent's trunk protector, body leaning forward over the support leg.

- 이름(ko): 태권도 뒤차기, 뒤차기 임팩트, 태권도 뒤돌아차기, 몸통 뒤차기
- names (en): taekwondo back kick, dwit chagi, spinning back kick, back kick impact

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #TAEKWONDO_BACK_KICK

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 59 deg, turned 68 deg to the athlete's right of the chest line; face pointing to the athlete's right and slightly backward and slightly up. Eyes on the target over the right shoulder.
- Torso: trunk line (hips to shoulders) 63 deg forward of vertical, leaning 31 deg to the athlete's right; spine flexed 5 deg over the pelvis; shoulder line rotated 39 deg to the right of the hip line (hip-shoulder separation).
- Right arm: upper arm raised 25 deg from the side of the trunk, pointing backward and down and slightly to the athlete's right; elbow fully folded (110 deg flexion); forearm pointing forward and slightly down; palm facing down and to the athlete's left; wrist neutral; hand: closed fist; fingertips 0.89 m above the floor.
- Left arm: upper arm raised 30 deg from the side of the trunk, pointing down and backward and slightly to the athlete's right; elbow deeply bent (110 deg flexion); forearm pointing forward and slightly to the athlete's right; palm facing to the athlete's right and slightly backward and slightly up; wrist neutral; hand: closed fist; fingertips 0.80 m above the floor.
- Right leg (kicking leg): hip extended 30 deg; knee slightly bent (21 deg flexion); thigh pointing backward, shin pointing backward and slightly up; ankle dorsiflexed 25 deg; foot 84 cm above the floor.
- Left leg (support leg): hip flexed 63 deg; knee slightly bent (25 deg flexion); thigh pointing down, shin pointing down and slightly backward; ankle dorsiflexed 20 deg; foot flat on the floor.
- Base: ankles 80 cm apart (44% of body height, 2.0x shoulder width); every support foot touches the floor, none floats.
- B (opponent in fighting stance): 105 cm backward and slightly to the athlete's right of the main athlete, turned side-on to the main athlete; trunk 10 deg forward of vertical; knees 12/20 deg (right/left); elbows 115/95 deg; both feet on the floor. Opponent in a closed fighting stance (left foot forward), guard up, electronic trunk protector on.
- Technique cue: look before you kick
- Technique cue: kick in a straight line, heel first
- Technique cue: toes point down, not to the side

3. OBJECT_INTERACTION:
- Legal under the WT rules: the kicking foot lands on the front or side of the trunk protector; the kicking foot is above the opponent's waist; neither fist is on the opponent's face.

4. CINEMATIC_CAMERA:
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view across the contest area, both athletes in profile.
- front_three_quarter: eye-level shot, three-quarter front view, 35mm standard lens, full-body shot. Three-quarter front view of the kicker, low and dynamic.
- low_cinema: camera 0.5 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot. Low wide frame from the mat, octagon edge and arena lights.

5. KINETIC_ENERGY:
- opponent folding at the waist on impact
- dobok jacket swinging with the spin
- trunk protector sensor lights
```

## Prompt (fill {SUBJECT}, {PARTNER_B} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a taekwondo athlete landing a spinning back kick on the opponent's trunk protector. Opposite the main athlete: {PARTNER_B} as the opponent in fighting stance. Back turned to the opponent, head turned to look over the right shoulder; body leaning forward over the bent left support leg; right leg thrust straight back at trunk height, foot flexed with the toes pointing down, heel and sole driving into the opponent's trunk protector; fists tucked in close to the chest. Look before you kick. Kick in a straight line, heel first. Toes point down, not to the side. Eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view across the contest area, both athletes in profile. Opponent folding at the waist on impact; dobok jacket swinging with the spin. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, black belt missing, trunk protector missing, kicking with the shin instead of the foot, bare chest, boxing gloves, southpaw stance, kicking foot turned sideways like a side kick, not looking at the target, kick landing with the shin, kick to the opponent's spine, kick to the opponent's leg or knee, punch to the opponent's face, hand grabbing the opponent's dobok, catching the opponent's kicking leg, knee strike, head butt
```

## Control images

- `openpose_side.png` / `.json`: 1344x768, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_front_three_quarter.png` / `.json`: 1152x896, eye-level shot, three-quarter front view, 35mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.5 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: head.flex = 59 is beyond the usual range -65..56

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_knee_flex | 21.1 | ..30 | kicking leg driven straight back | KUK, EST |
| z:r_heel | 1.1 | 0.8..1.35 | heel lands on the trunk protector | WT |

## Official game rules (World Taekwondo Competition Rules & Interpretation (Olympic sparring, kyorugi))

| rule | what | check on this skeleton |
|---|---|---|
| WT Permitted techniques and areas | Kick lands with the foot on the trunk protector: A kick scores only when the part of the foot below the ankle bone lands on a permitted area; the trunk protector may be attacked by fist and foot, but not the spine. | OK: r heel 1 cm from B.belly |
| WT Prohibited acts (gam-jeom): attacking below the waist | Attacking below the waist: Kicking or attacking the opponent below the waist is a gam-jeom (penalty point to the opponent). | OK: lowest of r_ankle +14 cm against the B.belt front |
| WT Prohibited acts (gam-jeom): hitting the head with the hand | Hand attack to the face: Hitting the opponent's head or face with the hand is a gam-jeom; the head may be attacked only by kicks. | OK: r knuckles 148 cm from B.nose |
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
