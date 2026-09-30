# BOXING_LEAD_HOOK

Orthodox boxer landing a left hook: elbow bent about 90 degrees with the forearm horizontal at shoulder height, pivoting on the lead foot, trunk turning right, fist on the opponent's jaw.

- 이름(ko): 권투 훅, 레프트 훅, 복싱 훅 펀치, 리드 훅
- names (en): boxing lead hook, left hook, hook punch, hook to the jaw

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BOXING_LEAD_HOOK

2. ANATOMICAL_BONES:
- Gaze & head: head level, turned 46 deg to the athlete's left of the chest line; face pointing to the athlete's left and forward. Eyes on the target.
- Torso: trunk line (hips to shoulders) 16 deg forward of vertical, leaning 5 deg to the athlete's right; spine flexed 8 deg over the pelvis; shoulder line rotated 11 deg to the right of the hip line (hip-shoulder separation).
- Right arm (rear glove at the chin): upper arm raised 64 deg from the side of the trunk, pointing forward and down and slightly to the athlete's left; elbow fully folded (121 deg flexion); forearm pointing up and slightly to the athlete's left; palm facing to the athlete's left and backward and slightly down; wrist neutral; hand: closed fist; fingertips 1.63 m above the floor.
- Left arm (hooking lead arm): upper arm raised 80 deg from the side of the trunk, pointing to the athlete's left; elbow bent to about a right angle (96 deg flexion); forearm pointing forward and slightly up; palm facing down and slightly to the athlete's right and slightly forward; wrist neutral; hand: closed fist; fingertips 1.58 m above the floor.
- Right leg: hip flexed 12 deg; knee slightly bent (10 deg flexion); thigh pointing down, shin pointing down; ankle neutral; foot flat on the floor.
- Left leg: hip flexed 22 deg; knee slightly bent (25 deg flexion); thigh pointing down, shin pointing down; ankle neutral; on the ball of the foot, heel raised.
- Base: ankles 38 cm apart (21% of body height, 1.0x shoulder width); every support foot touches the floor, none floats.
- B (opponent in orthodox guard): 73 cm forward and slightly to the athlete's left of the main athlete, turned side-on to the main athlete; trunk 12 deg forward of vertical; knees 19/22 deg (right/left); elbows 142/142 deg; both feet on the floor. Opponent in a high guard, gloves at the cheekbones, chin tucked.
- Technique cue: turn on the lead ball of the foot
- Technique cue: elbow at shoulder height, 90-degree arm
- Technique cue: keep the rear hand at the chin

3. OBJECT_INTERACTION:
- Legal under the World Boxing rules: both gloves stay above the opponent's belt line; both hands are closed fists inside the gloves.

4. CINEMATIC_CAMERA:
- ringside: eye-level shot, side profile view, 50mm standard lens, full-body shot. Ringside view across the ropes, both boxers in profile.
- over_shoulder: eye-level shot, from behind, 35mm standard lens, full-body shot. Over the shoulder of the puncher, the opponent's face in focus.
- low_cinema: camera 0.9 m above the floor, three-quarter front view, 24mm wide-angle lens, full-body shot. Low wide frame from the canvas, ring lights and ropes above.

5. KINETIC_ENERGY:
- opponent's head turning with the impact, sweat and water spray
- motion blur along the arc of the hook
- crowd flashes
```

## Prompt (fill {SUBJECT}, {PARTNER_B} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, an orthodox boxer landing a left hook on the opponent's jaw. Opposite the main athlete: {PARTNER_B} as the opponent in orthodox guard. Left arm bent about 90 degrees with the forearm horizontal at shoulder height, fist landing on the side of the opponent's jaw; pivoting on the ball of the left foot, heel turning out; trunk turning to the right; right glove at the right cheek. Turn on the lead ball of the foot. Elbow at shoulder height, 90-degree arm. Keep the rear hand at the chin. Eye-level shot, side profile view, 50mm standard lens, full-body shot. Ringside view across the ropes, both boxers in profile. Opponent's head turning with the impact, sweat and water spray; motion blur along the arc of the hook. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, open hands inside the gloves, bent wrist at impact, gloves merged together, both feet together, chin up, southpaw stance, looping open arm, hook thrown with a straight arm, punch landing below the belt, slapping with an open glove, backhand blow, head butting the opponent, elbow strike to the face, punch to the back of the head, boxers clinching and holding, arm locked around the opponent's neck
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
| l_elbow_flex | 96.3 | 70..110 | elbow about 90 deg, forearm horizontal | EST |
| l_shoulder_elev | 80.0 | 65..100 | elbow raised to shoulder height | EST |

## Official game rules (World Boxing Technical and Competition Rules (Olympic-style boxing, carried over from the AIBA rules))

| rule | what | check on this skeleton |
|---|---|---|
| World Boxing Fouls: hitting below the belt | Hitting below the belt: Blows must land on the front or sides of the head or body above the belt line; hitting below the belt is a foul. | OK: lowest of r_knuckles/l_knuckles +58 cm against the B.belt front |
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
