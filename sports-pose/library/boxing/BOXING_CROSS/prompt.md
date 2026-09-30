# BOXING_CROSS

Orthodox boxer landing a right cross: rear heel up and pivoting, hips and shoulders turned square, rear arm extended to the opponent's chin, lead glove back at the chin.

- 이름(ko): 권투 크로스, 라이트 스트레이트, 원투 펀치, 복싱 스트레이트
- names (en): boxing cross, right straight, rear straight punch, one-two

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BOXING_CROSS

2. ANATOMICAL_BONES:
- Gaze & head: head level; face pointing forward and slightly down. Eyes on the target.
- Torso: trunk line (hips to shoulders) 20 deg forward of vertical; spine flexed 10 deg over the pelvis; shoulder line rotated 20 deg to the left of the hip line (hip-shoulder separation).
- Right arm (punching rear hand): upper arm raised 115 deg from the side of the trunk, pointing forward; elbow slightly bent (20 deg flexion); forearm pointing forward and slightly up; palm facing down and slightly forward; wrist neutral; hand: closed fist; fingertips 1.55 m above the floor.
- Left arm (lead glove back at the chin): upper arm raised 62 deg from the side of the trunk, pointing down and forward; elbow fully folded (138 deg flexion); forearm pointing up; palm facing to the athlete's right and backward; wrist neutral; hand: closed fist; fingertips 1.59 m above the floor.
- Right leg: hip extended 14 deg; knee slightly bent (16 deg flexion); thigh pointing down and slightly backward, shin pointing down and backward; ankle neutral; on the ball of the foot, heel raised.
- Left leg: hip flexed 30 deg; knee bent (32 deg flexion); thigh pointing down and slightly forward, shin pointing down; ankle dorsiflexed 12 deg; foot flat on the floor.
- Base: ankles 70 cm apart (39% of body height, 1.7x shoulder width); every support foot touches the floor, none floats.
- B (opponent in orthodox guard): 95 cm forward and slightly to the athlete's right of the main athlete, facing the main athlete; trunk 12 deg forward of vertical; knees 18/22 deg (right/left); elbows 142/142 deg; both feet on the floor. Opponent in a high guard, gloves at the cheekbones, chin tucked.
- Technique cue: rear heel up, turn the hip
- Technique cue: rear shoulder covers the chin
- Technique cue: lead hand back to the chin

3. OBJECT_INTERACTION:
- Legal under the World Boxing rules: both gloves stay above the opponent's belt line; both hands are closed fists inside the gloves.

4. CINEMATIC_CAMERA:
- ringside: eye-level shot, side profile view, 50mm standard lens, full-body shot. Ringside view across the ropes, both boxers in profile.
- over_shoulder: eye-level shot, from behind, 35mm standard lens, full-body shot. Over the shoulder of the puncher, the opponent's face in focus.
- low_cinema: camera 0.9 m above the floor, three-quarter front view, 24mm wide-angle lens, full-body shot. Low wide frame from the canvas, ring lights and ropes above.

5. KINETIC_ENERGY:
- opponent's head snapping back, sweat spray
- motion blur on the punching arm
- canvas dust under the pivoting foot
```

## Prompt (fill {SUBJECT}, {PARTNER_B} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, an orthodox boxer landing a right cross to the opponent's chin. Opposite the main athlete: {PARTNER_B} as the opponent in orthodox guard. Rear right foot pivoting on the ball with the heel up and knee turned in; hips and shoulders turned square to the opponent; right arm fully extended, fist palm down on the chin; right shoulder raised; left glove pulled back to the left cheek; weight shifting onto the front leg. Rear heel up, turn the hip. Rear shoulder covers the chin. Lead hand back to the chin. Eye-level shot, side profile view, 50mm standard lens, full-body shot. Ringside view across the ropes, both boxers in profile. Opponent's head snapping back, sweat spray; motion blur on the punching arm. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, open hands inside the gloves, bent wrist at impact, gloves merged together, both feet together, chin up, southpaw stance, rear foot flat during the cross, punch landing below the belt, slapping with an open glove, backhand blow, head butting the opponent, elbow strike to the face, punch to the back of the head, boxers clinching and holding, arm locked around the opponent's neck
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
| r_elbow_flex | 20.0 | ..20 | rear arm extended, soft not locked | EST |
| r_foot_pitch | 40.0 | 20.. | rear heel up, pivoting on the ball of the foot | EST |
| l_elbow_flex | 137.5 | 100.. | lead glove back at the chin | EST |

## Official game rules (World Boxing Technical and Competition Rules (Olympic-style boxing, carried over from the AIBA rules))

| rule | what | check on this skeleton |
|---|---|---|
| World Boxing Fouls: hitting below the belt | Hitting below the belt: Blows must land on the front or sides of the head or body above the belt line; hitting below the belt is a foul. | OK: lowest of r_knuckles/l_knuckles +53 cm against the B.belt front |
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
- [FR24] Uppercut biomechanics review 2024: pelvic rotation and lower-limb push-off drive the punch https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2024.1441470/pdf
- [EST] Estimate from standard boxing coaching (no measured joint angle found this session) 
