# BOXING_JAB

Orthodox boxer landing a jab: lead arm extended at shoulder height, fist turned palm down on the opponent's face, lead shoulder raised to protect the chin, rear glove guarding the chin.

- 이름(ko): 권투 잽, 복싱 잽 펀치, 잽 임팩트, 리드 스트레이트
- names (en): boxing jab, lead straight punch, jab landing, jab extension

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BOXING_JAB

2. ANATOMICAL_BONES:
- Gaze & head: head level, turned 42 deg to the athlete's left of the chest line; face pointing forward and to the athlete's left. Eyes on the target through the gloves.
- Torso: trunk line (hips to shoulders) 16 deg forward of vertical; spine flexed 8 deg over the pelvis; shoulder line rotated 11 deg to the right of the hip line (hip-shoulder separation).
- Right arm (rear hand guarding the chin): upper arm raised 63 deg from the side of the trunk, pointing down and forward and slightly to the athlete's left; elbow fully folded (121 deg flexion); forearm pointing up and slightly to the athlete's left; palm facing backward and to the athlete's left; wrist neutral; hand: closed fist; fingertips 1.62 m above the floor.
- Left arm (punching lead hand): upper arm raised 110 deg from the side of the trunk, pointing to the athlete's left and forward; elbow straight (4 deg flexion); forearm pointing to the athlete's left and forward; palm facing backward and to the athlete's left; wrist neutral; hand: closed fist; fingertips 1.55 m above the floor.
- Right leg: hip extended 6 deg; knee slightly bent (14 deg flexion); thigh pointing down, shin pointing down and slightly backward; ankle dorsiflexed 8 deg; on the ball of the foot, heel raised.
- Left leg: hip flexed 25 deg; knee slightly bent (25 deg flexion); thigh pointing down and slightly forward, shin pointing down; ankle neutral; foot flat on the floor.
- Base: ankles 50 cm apart (28% of body height, 1.3x shoulder width); every support foot touches the floor, none floats.
- B (opponent in orthodox guard): 110 cm to the athlete's left and forward of the main athlete, facing the main athlete; trunk 12 deg forward of vertical; knees 18/22 deg (right/left); elbows 142/142 deg; both feet on the floor. Opponent in a high guard, gloves at the cheekbones, chin tucked.
- Technique cue: turn the jab over, palm down
- Technique cue: lead shoulder protects the chin
- Technique cue: return the punch along the line it went out

3. OBJECT_INTERACTION:
- Legal under the World Boxing rules: both gloves stay above the opponent's belt line; both hands are closed fists inside the gloves.

4. CINEMATIC_CAMERA:
- ringside: eye-level shot, side profile view, 50mm standard lens, full-body shot. Ringside view across the ropes, both boxers in profile.
- over_shoulder: eye-level shot, from behind, 35mm standard lens, full-body shot. Over the shoulder of the puncher, the opponent's face in focus.
- low_cinema: camera 0.9 m above the floor, three-quarter front view, 24mm wide-angle lens, full-body shot. Low wide frame from the canvas, ring lights and ropes above.

5. KINETIC_ENERGY:
- sweat spraying off the opponent's head at impact
- glove slightly compressed on contact
- ring lights flaring
```

## Prompt (fill {SUBJECT}, {PARTNER_B} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, an orthodox boxer landing a stiff jab on the opponent's face. Opposite the main athlete: {PARTNER_B} as the opponent in orthodox guard. Left lead arm fully extended at shoulder height, fist turned palm down, knuckles on the opponent's face; left shoulder raised against the chin; right glove held at the right cheek; feet staggered, rear heel up. Turn the jab over, palm down. Lead shoulder protects the chin. Return the punch along the line it went out. Eye-level shot, side profile view, 50mm standard lens, full-body shot. Ringside view across the ropes, both boxers in profile. Sweat spraying off the opponent's head at impact; glove slightly compressed on contact. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, open hands inside the gloves, bent wrist at impact, gloves merged together, both feet together, chin up, southpaw stance, jab thrown with the right hand, punch landing below the belt, slapping with an open glove, backhand blow, head butting the opponent, elbow strike to the face, punch to the back of the head, boxers clinching and holding, arm locked around the opponent's neck
```

## Control images

- `openpose_ringside.png` / `.json`: 1344x768, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_over_shoulder.png` / `.json`: 1152x896, eye-level shot, from behind, 35mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.9 m above the floor, three-quarter front view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| l_elbow_flex | 3.8 | ..20 | lead arm extended, soft not locked | EST |
| r_elbow_flex | 121.0 | 115.. | rear glove stays at the chin | EST |

## Official game rules (World Boxing Technical and Competition Rules (Olympic-style boxing, carried over from the AIBA rules))

| rule | what | check on this skeleton |
|---|---|---|
| World Boxing Fouls: hitting below the belt | Hitting below the belt: Blows must land on the front or sides of the head or body above the belt line; hitting below the belt is a foul. | OK: lowest of r_knuckles/l_knuckles +57 cm against the B.belt front |
| World Boxing Scoring blows; Fouls: open glove | Knuckle part of the closed glove: A scoring blow lands with the knuckle part of the closed glove; hitting with the open glove, the inside of the glove, the wrist or the side of the hand is a foul. | OK: r hand is fist; l hand is fist |
| World Boxing Fouls: head, shoulder, forearm, elbow | Head butts and elbows: Butting, or attacking with the head, shoulder, forearm or elbow, is a foul; only the fist in the glove may strike. | text only |
| World Boxing Fouls: back of the head, neck, kidneys | Rabbit punch and kidney punch: Blows to the back of the head or neck and to the kidneys are fouls; the target is the front and sides of the head and body. | text only |
| World Boxing Fouls: holding, pushing, wrestling | Holding and wrestling: Holding, hooking the opponent's arm or neck, pushing, tripping, wrestling or throwing is a foul, and so is holding and hitting at the same time. | text only |

Scene rules for a full match shot (players, uniforms, officials):

- Square ring with four ropes, one red corner, one blue corner and two white neutral corners; the canvas covers a padded floor. (World Boxing Ring)
- Each boxer wears the colour of the corner (red or blue) on the vest, shorts, gloves and headguard; the waistband of the shorts marks the belt line and must be clearly visible. (World Boxing Uniform)
- Mouthguard in every bout; hand wraps under the gloves; groin guard; elite men usually box without headguards (women, youth and juniors often wear them, check the event). (World Boxing Personal equipment)
- One referee inside the ring; judges seated at ringside; each boxer has a coach in the corner. (World Boxing Officials)

Rulebook: https://www.worldboxing.org

## Sources

- [ST18] Stanley et al. 2018: 3D punch kinematics of 15 amateur boxers (lead hook fastest fist 11.95 m/s; jab quickest) https://ideas.repec.org/a/taf/rpanxx/v18y2018i5p835-854.html
- [EST] Estimate from standard boxing coaching (no measured joint angle found this session) 
