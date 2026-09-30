# BOXING_GUARD_STANCE

Orthodox boxing guard: left foot and left hand forward, feet about shoulder width, knees soft, rear heel slightly raised, gloves at the cheekbones, elbows tucked, chin down.

- 이름(ko): 권투 가드 자세, 복싱 기본 자세, 오소독스 스탠스, 복싱 가드
- names (en): boxing guard stance, orthodox stance, fighting stance boxing, high guard

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BOXING_GUARD_STANCE

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 15 deg, turned 30 deg to the athlete's left of the chest line; face pointing forward and slightly to the athlete's left and slightly down. Eyes on the opponent.
- Torso: trunk line (hips to shoulders) 12 deg forward of vertical; spine flexed 6 deg over the pelvis; shoulders square with the hips.
- Right arm (rear hand): upper arm raised 61 deg from the side of the trunk, pointing forward and down; elbow fully folded (130 deg flexion); forearm pointing up and slightly to the athlete's left; palm facing to the athlete's left and slightly down; wrist neutral; hand: closed fist; fingertips 1.59 m above the floor.
- Left arm (lead hand): upper arm raised 63 deg from the side of the trunk, pointing forward and down and slightly to the athlete's right; elbow fully folded (145 deg flexion); forearm pointing up; palm facing to the athlete's right and slightly backward; wrist neutral; hand: closed fist; fingertips 1.65 m above the floor.
- Right leg: hip extended 3 deg; knee slightly bent (19 deg flexion); thigh pointing down, shin pointing down and slightly backward; ankle dorsiflexed 12 deg; foot flat on the floor.
- Left leg (lead leg): hip flexed 22 deg; knee slightly bent (22 deg flexion); thigh pointing down and slightly forward, shin pointing down; ankle neutral; foot flat on the floor.
- Base: ankles 46 cm apart (26% of body height, 1.1x shoulder width); every support foot touches the floor, none floats.
- Technique cue: chin down, hands up to the cheekbones, elbows in
- Technique cue: weight balanced on the balls of the feet
- Technique cue: lead foot toe points at the opponent

3. OBJECT_INTERACTION:
- Legal under the World Boxing rules: both hands are closed fists inside the gloves.

4. CINEMATIC_CAMERA:
- front: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. Opponent's view, gloves framing the eyes.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Profile: stance width and tucked elbows.
- low_cinema: camera 0.8 m above the floor, three-quarter front view, 24mm wide-angle lens, full-body shot. Low wide frame, ring ropes and lights.

5. KINETIC_ENERGY:
- sweat on the shoulders under the ring lights
- hand wraps visible at the wrists
- slight bounce in the knees
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a boxer in an orthodox guard stance. Left foot forward and right foot back about shoulder width apart, knees soft, rear heel slightly raised; body turned side-on about 35 degrees; both gloves up at the cheekbones, elbows tucked against the ribs; chin down, eyes looking up through the brows. Chin down, hands up to the cheekbones, elbows in. Weight balanced on the balls of the feet. Lead foot toe points at the opponent. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. Opponent's view, gloves framing the eyes. Sweat on the shoulders under the ring lights; hand wraps visible at the wrists. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, open hands inside the gloves, bent wrist at impact, gloves merged together, both feet together, chin up, southpaw stance, slapping with an open glove, backhand blow, boxers clinching and holding, arm locked around the opponent's neck, boxer ducking with the head at waist height
```

## Control images

- `openpose_front.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_side.png` / `.json`: 896x1152, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.8 m above the floor, three-quarter front view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_elbow_flex | 130.0 | 115.. | rear glove held at the cheek, elbow tucked | EST |
| l_elbow_flex | 145.0 | 100.. | lead glove up at eye height | EST |
| r_knee_flex | 18.5 | 10..40 | knees soft, never locked | EST |
| stance_over_shoulders | 1.1 | 0.9..1.8 | feet about shoulder width apart, staggered | EST |

## Official game rules (World Boxing Technical and Competition Rules (Olympic-style boxing, carried over from the AIBA rules))

| rule | what | check on this skeleton |
|---|---|---|
| World Boxing Scoring blows; Fouls: open glove | Knuckle part of the closed glove: A scoring blow lands with the knuckle part of the closed glove; hitting with the open glove, the inside of the glove, the wrist or the side of the hand is a foul. | OK: r hand is fist; l hand is fist |
| World Boxing Fouls: holding, pushing, wrestling | Holding and wrestling: Holding, hooking the opponent's arm or neck, pushing, tripping, wrestling or throwing is a foul, and so is holding and hitting at the same time. | text only |
| World Boxing Fouls: ducking below the belt | Ducking below the belt: Ducking so low that the head goes below the opponent's belt line is a foul. | text only |

Scene rules for a full match shot (players, uniforms, officials):

- Square ring with four ropes, one red corner, one blue corner and two white neutral corners; the canvas covers a padded floor. (World Boxing Ring)
- Each boxer wears the colour of the corner (red or blue) on the vest, shorts, gloves and headguard; the waistband of the shorts marks the belt line and must be clearly visible. (World Boxing Uniform)
- Mouthguard in every bout; hand wraps under the gloves; groin guard; elite men usually box without headguards (women, youth and juniors often wear them, check the event). (World Boxing Personal equipment)
- One referee inside the ring; judges seated at ringside; each boxer has a coach in the corner. (World Boxing Officials)

Rulebook: https://www.worldboxing.org

## Sources

- [EST] Estimate from standard boxing coaching (no measured joint angle found this session) 
