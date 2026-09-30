# BASKETBALL_JUMP_SHOT_SET

Right-handed basketball jump shot at the set point: knees bent, ball set above the right eye, shooting elbow under the ball, guide hand on the side, eyes on the rim.

- 이름(ko): 농구 점프슛 셋, 슛 준비 자세, 슈팅 셋 포인트, 점프슛 준비
- names (en): basketball jump shot set, shot set point, shooting pocket, jumper wind-up

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASKETBALL_JUMP_SHOT_SET

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 11 deg; face pointing forward. Eyes on the rim, looking under the ball.
- Torso: trunk line (hips to shoulders) 18 deg forward of vertical; shoulders square with the hips.
- Right arm (shooting arm, elbow under the ball): upper arm raised 100 deg from the side of the trunk, pointing forward and slightly to the athlete's left; elbow bent to about a right angle (98 deg flexion); forearm pointing up; palm facing up and slightly forward; wrist extended (cocked back) 68 deg; hand: fingers spread around the ball, palm not touching it fully; fingertips 1.69 m above the floor.
- Left arm (guide hand on the side of the ball): upper arm raised 131 deg from the side of the trunk, pointing forward and slightly up; elbow bent to about a right angle (84 deg flexion); forearm pointing to the athlete's right and up; palm facing to the athlete's right; wrist extended (cocked back) 46 deg; hand: fingers spread around the ball, palm not touching it fully; fingertips 1.91 m above the floor.
- Right leg (shooting-side foot slightly ahead): hip flexed 42 deg, abducted 15 deg; knee bent (62 deg flexion); thigh pointing down and slightly forward and slightly to the athlete's right, shin pointing down and backward; ankle dorsiflexed 35 deg; foot flat on the floor.
- Left leg: hip flexed 41 deg, abducted 15 deg; knee bent (62 deg flexion); thigh pointing down and slightly forward and slightly to the athlete's left, shin pointing down and backward; ankle dorsiflexed 36 deg; foot flat on the floor.
- Base: ankles 43 cm apart (23% of body height, 1.0x shoulder width); every support foot touches the floor, none floats.
- Technique cue: balance: feet shoulder-width, shooting-side foot slightly ahead
- Technique cue: elbow under the ball, forearm vertical
- Technique cue: fingers spread, ball on the finger pads
- Technique cue: eyes on the rim, not on the ball

3. OBJECT_INTERACTION:
- ball (24 cm diameter): center 1.78 m above the floor; surface 10 cm from the forehead (forward and up and slightly to the athlete's right of it).
- Rim 3.05 m high, 480 cm ahead (mid-range shot); the ball is set 14 cm above and 14 cm in front of the forehead.
- Legal under the FIBA rules: no body contact with an opponent outside the player's own cylinder; no other player touches the ball on its downward flight above the ring; jersey tucked into the shorts.

4. CINEMATIC_CAMERA:
- front: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From under the basket: shooting elbow directly under the ball, both eyes on the rim.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Profile: vertical forearm, bent knees, ball above the eyes.
- wide_cinema: eye-level shot, three-quarter rear view, 28mm wide-angle lens, full-body shot. Over-the-shoulder wide shot toward the basket, arena lights and crowd behind.

5. KINETIC_ENERGY:
- legs loaded, calves tense
- ball rotation seams sharp and still
- sweat on the forearm catching the arena lights
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a basketball player setting a right-handed jump shot, ball raised above the right eye. Feet shoulder-width and flat, right foot slightly ahead, both toes pointing at the basket, knees bent about 65 degrees; ball set just above and in front of the forehead on the right side; shooting hand under the ball with the wrist bent back so the ball rests on the finger pads, a small gap under the palm; shooting elbow directly under the ball, forearm vertical; left guide hand on the left side of the ball, fingers up. Balance: feet shoulder-width, shooting-side foot slightly ahead. Elbow under the ball, forearm vertical. Fingers spread, ball on the finger pads. Eyes on the rim, not on the ball. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From under the basket: shooting elbow directly under the ball, both eyes on the rim. Legs loaded, calves tense; ball rotation seams sharp and still. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, elbow flared out to the side, ball flat in the palm, ball behind the head, guide hand pushing from behind, fingers fused into the ball, heels floating, untucked jersey, headband wider than 10 cm
```

## Control images

- `openpose_front.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_side.png` / `.json`: 896x1152, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, eye-level shot, three-quarter rear view, 28mm wide-angle lens, full-body shot.

## Checks

- warn: r_leg.ankle = -35 is beyond the usual range -35..60
- warn: l_leg.ankle = -36 is beyond the usual range -35..60

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_knee_flex | 62.0 | 55..75 | knees flexed about 64-70 deg (inside angle 110-116 deg) in proficient shooters | S1 |
| r_elbow_flex | 97.9 | 90..135 | shooting elbow deeply bent at the set (inside angle about 50-72 deg) | S1, S2 |
| r_forearm_tilt | 2.1 | ..20 | shooting forearm nearly vertical (about 8 deg), elbow under the ball | S2 |
| fwd:ball:forehead | 14.0 | 3..30 | ball in front of the forehead, not behind the head | S3 |
| r_foot_z | 0.0 | ..0.03 | feet on the floor at the set | S4 |
| l_foot_z | 0.0 | ..0.03 | feet on the floor at the set | S4 |
| stance_over_shoulders | 1.0 | 0.8..1.5 | feet about shoulder-width | S4 |

## Official game rules (FIBA Official Basketball Rules 2024 and FIBA Basketball Equipment (OBR 2026 takes effect on 1 October 2026: free line colours, visible-sock rule removed, unsportsmanlike foul renamed; article numbers may move))

| rule | what | check on this skeleton |
|---|---|---|
| FIBA Art. 33.1, 33.2 | Cylinder and verticality: Each player owns the vertical space above their position; a player who leaves their cylinder and makes contact is responsible for it. | text only |
| FIBA Art. 33.6 | Landing space: A player who has jumped has the right to land at the same place (or at a spot not occupied by an opponent at take-off). | text only |
| FIBA Art. 31.2 | Goaltending and basket interference: Touching a shot on its downward flight completely above the ring, or touching the ring or backboard while the ball is on the ring, is a violation. | text only |
| FIBA Art. 4.3, 4.4 | Uniform: Shirts tucked in; sleeves, headbands, wristbands and tape of one solid team colour. | text only |
| equipment | ring_height | OK: height_m 3.05 (official 3.044-3.056, FIBA Equipment (3.05 m to the top of the ring)) |
| equipment | ball_size | OK: diameter_m 0.24 (official 0.2384-0.2483, FIBA Equipment (size 7: 749-780 mm around; size 6: 724-737 mm)) |

Scene rules for a full match shot (players, uniforms, officials):

- Five players per team on the court. (FIBA Art. 4.2.2)
- Home team in light (preferably white) shirts, visiting team in dark shirts; shirts tucked into the shorts; all sleeves, headbands, wristbands and tape on a team in the same solid colour, headbands at most 10 cm wide. (FIBA Art. 4.3)
- Shirt numbers only 0, 00 or 1-99: at least 20 cm tall on the back and 10 cm on the front. (FIBA Art. 4.3.2)
- A crew chief and one or two umpires in grey officials' shirts on the court; scorer, timer and shot-clock operator at the table. (FIBA Art. 45)
- Shot clocks mounted above and behind each backboard (red digits); backboard 1.80 x 1.05 m with its lower edge 2.90 m up, 1.20 m in from the endline; ring 3.05 m high with a 40-45 cm net. (FIBA Equipment)
- Court 28 x 15 m with 5 cm lines, three-point arc 6.75 m (6.60 m in the corners), free-throw line 5.80 m from the endline, no-charge semi-circle 1.25 m under the basket. (FIBA Art. 2.4)

Rulebook: https://refereeing.fiba.basketball/en/rules

## Sources

- [S1] Cabarkapa et al. 2022, Sports 10(1):2: knee 110-116 deg, hip 128-137 deg, elbow 49-50 deg inside angles, proficient shooters https://doi.org/10.3390/sports10010002
- [S2] Cabarkapa et al. 2021, CEJSSM: free throw set, elbow 72 deg inside angle, forearm 8 deg from vertical https://wnus.usz.edu.pl/cejssm/file/article/download/19306/78716.pdf
- [S3] FIBA WABC Level 1 manual 2.7.5: shooting hand and elbow under the ball, guide hand on the side, look under the ball at the rim https://wabc.fiba.com/manual/level-1/l1-player/l1-2-offensive-basketball-skills/2-7-shooting/2-7-5-basic-shooting-top-of-the-shot-releasing-the-ball/
- [S4] FIBA WABC Level 1 manual 2.7.7: jump shot, feet pointing at the basket, balanced stance https://wabc.fiba.com/manual/level-1/l1-player/l1-2-offensive-basketball-skills/2-7-shooting/2-7-7-basic-shooting-jump-shot/
