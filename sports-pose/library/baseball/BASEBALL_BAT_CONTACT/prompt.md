# BASEBALL_BAT_CONTACT

Right-handed batter at bat-ball contact: hips and shoulders square to the pitcher, front leg firm, back shoulder low, rear elbow tucked, barrel about 30 degrees below the hands meeting the ball.

- 이름(ko): 야구 타격 임팩트, 배트 공 맞는 순간, 타격 순간, 스윙 임팩트
- names (en): baseball bat contact, hitting impact, bat on ball, swing contact

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASEBALL_BAT_CONTACT

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 16 deg, turned 29 deg to the athlete's right of the chest line; face pointing forward and slightly down and slightly to the athlete's right. Head down and still, eyes on the ball at contact.
- Torso: trunk line (hips to shoulders) 7 deg forward of vertical, leaning 28 deg to the athlete's right; spine arched back (extended) 5 deg over the pelvis; shoulders square with the hips.
- Right arm (rear arm, top hand): upper arm raised 16 deg from the side of the trunk, pointing down and slightly to the athlete's left; elbow bent to about a right angle (79 deg flexion); forearm pointing forward; palm facing up and slightly to the athlete's left; wrist neutral; hand: fingers wrapped firmly around what it holds; fingertips 0.77 m above the floor.
- Left arm (lead arm, bottom hand on the bat): upper arm raised 47 deg from the side of the trunk, pointing down and slightly forward; elbow bent (38 deg flexion); forearm pointing to the athlete's right and down and slightly forward; palm facing down and slightly backward; wrist extended (cocked back) 12 deg; hand: fingers wrapped firmly around what it holds; fingertips 0.82 m above the floor.
- Right leg (rear leg): hip extended 7 deg; knee bent (58 deg flexion); thigh pointing down and slightly backward and slightly to the athlete's left, shin pointing backward and slightly down and slightly to the athlete's right; ankle dorsiflexed 11 deg; on the ball of the foot, heel raised.
- Left leg (stride leg (toward the pitcher)): hip flexed 56 deg; knee slightly bent (24 deg flexion); thigh pointing down and forward, shin pointing down and slightly forward; ankle plantar-flexed (toes pointed) 19 deg; foot flat on the floor.
- Base: ankles 99 cm apart (54% of body height, 2.4x shoulder width); every support foot touches the floor, none floats.
- Technique cue: firm front leg
- Technique cue: hips and shoulders square at contact
- Technique cue: hands above the barrel
- Technique cue: contact roughly level with the front foot

3. OBJECT_INTERACTION:
- bat (85 cm): gripped at the handle, barrel pointing to the athlete's right and slightly down; sweet spot 0.53 m above the floor.
- ball (7 cm diameter): center 0.53 m above the floor; surface 3 cm from the bat sweet (forward of it); surface 98 cm from the left ankle (to the athlete's right and slightly up of it).
- Home plate (43 cm wide, white) in front of the batter; the batter stands inside the 1.22 x 1.83 m batter's box drawn 15 cm from the plate; catcher and plate umpire behind.
- Legal under the OBR rules: both feet are inside the batter's box; the batter wears a batting helmet with an ear flap.

4. CINEMATIC_CAMERA:
- pitcher_view: eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast center-field view, telephoto compression, catcher and umpire soft behind.
- open_side: eye-level shot, side profile view, 50mm standard lens, full-body shot. From the open side facing the batter's chest, plate in the foreground.
- low_cinema: camera 0.3 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot. Low wide frame from behind the catcher's area, stadium lights and field behind.

5. KINETIC_ENERGY:
- ball compressing against the barrel, wood chips of dust
- extreme motion blur along the bat's arc, hands sharp
- back heel lifted, dirt spraying from the pivot
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed baseball batter hitting the ball at the moment of bat-ball contact. Hips and shoulders turned square to the pitcher; front (left) leg straight and firm; back knee bent, back foot pivoted up on its toes; trunk tilted so the back shoulder is lower than the front; both hands together on the handle, right hand on top; rear elbow tucked close to the ribs; bat nearly perpendicular to the pitch line with the barrel about 30 degrees below the hands, sweet spot meeting the ball in front of the plate at about knee-to-thigh height. Firm front leg. Hips and shoulders square at contact. Hands above the barrel. Contact roughly level with the front foot. Eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast center-field view, telephoto compression, catcher and umpire soft behind. Ball compressing against the barrel, wood chips of dust; extreme motion blur along the bat's arc, hands sharp. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, bat merging with the hands, extra hands, bent bat, ball fused to the bat, left hand on top, rear foot flat, eyes off the ball, batter's foot outside the chalk box, batter without a helmet, batter wearing a cap instead of a helmet
```

## Control images

- `openpose_pitcher_view.png` / `.json`: 1152x896, eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot.
- `openpose_open_side.png` / `.json`: 1152x896, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.3 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| l_knee_flex | 24.0 | ..25 | front leg firm, knee about 14 deg | OBP-H |
| r_knee_flex | 58.0 | 55..85 | rear knee about 70 deg | OBP-H |
| r_elbow_flex | 78.8 | 65..95 | rear elbow tucked at about 80 deg | OBP-H, DOW16 |
| l_elbow_flex | 37.9 | 35..70 | lead elbow about 53 deg | OBP-H |
| r_shoulder_elev | 15.8 | 15..45 | rear shoulder abducted about 29-35 deg (elbow in) | OBP-H, DOW16 |
| hip_shoulder_sep | -3.7 | -12..12 | hips and shoulders square at contact | OBP-H |
| dist:r_palm:l_palm | 9.2 | ..14 | both hands together on the handle | OBP-H |
| l_foot_z | -0.0 | ..0.03 | front foot planted | OBP-H |

## Official game rules (MLB Official Baseball Rules (2025 edition; values unchanged for many seasons))

| rule | what | check on this skeleton |
|---|---|---|
| OBR 6.03(a)(1), 5.04(b)(5) | Feet in the batter's box: A batter who hits the ball with one or both feet on the ground entirely outside the batter's box is out; the lines belong to the box. | OK: inside |
| OBR 3.08 | Batting helmet: Every player at bat or running the bases wears a protective batting helmet. | text only |
| OBR Definitions of Terms (strike zone) | Strike zone: Over home plate, from the hollow beneath the kneecap up to the midpoint between the top of the shoulders and the top of the uniform pants, judged from the batter's stance. | text only |
| equipment | ball_size | OK: diameter_m 0.074 (official 0.0728-0.0748, OBR 3.01 (9-9.25 in around)) |
| equipment | bat_length | OK: length_m 0.85 (official 0.6-1.067, OBR 3.02(a) (at most 42 in)) |

Scene rules for a full match shot (players, uniforms, officials):

- Nine fielders per team. (OBR 1.01)
- The catcher crouches directly behind home plate in the catcher's box; the plate umpire (umpire-in-chief) stands behind the catcher; base umpires stand where they see the bases. (OBR 5.02(a), 8.03)
- All fielders except the catcher stand in fair territory; with the pitcher on the rubber, two infielders are on each side of second base with both feet on the infield dirt. (OBR 5.02(c))
- Batters, base runners and base coaches wear batting helmets (ear flap); the catcher wears a helmet and mask. (OBR 3.08)
- The pitcher's glove is not white or grey (piping excepted) and carries no other-coloured material; nothing is attached to the pitching hand, fingers or wrists (no tape, bandage or bracelet). (OBR 3.07(a), 6.02(c)(7))
- Home plate is a white five-sided slab 43 cm wide; the white pitcher's plate (61 x 15 cm) sits on a mound 25 cm above home plate, 18.44 m away. (OBR 2.02, 2.04)

Rulebook: https://mktg.mlbstatic.com/mlb/official-information/2025-official-baseball-rules.pdf

## Sources

- [OBP-H] Driveline OpenBiomechanics, baseball_hitting (98 hitters, 677 swings): means from the dataset (CC BY-NC-SA 4.0; only summary numbers used here) https://github.com/drivelineresearch/openbiomechanics/tree/main/baseball_hitting
- [DOW16] Dowling & Fleisig 2016, Sports Biomech: rear elbow about 78 deg and rear shoulder abduction about 35 deg at contact in pros https://www.tandfonline.com/doi/abs/10.1080/14763141.2016.1159320
- [FL13] Fleisig et al. 2013, Sports Biomech: hip-shoulder separation peaks after contact in pro batters https://www.tandfonline.com/doi/abs/10.1080/14763141.2013.838693
