# BASKETBALL_JUMP_SHOT_RELEASE

Right-handed basketball jump shot at release: airborne near the top of the jump, shooting arm extended high toward the rim, wrist snapped down in a gooseneck follow-through, guide hand up at the side.

- 이름(ko): 농구 점프슛 릴리스, 슛 팔로스루, 슛 쏘는 순간, 구스넥 팔로스루
- names (en): basketball jump shot release, shot follow-through, gooseneck, jumper release

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASKETBALL_JUMP_SHOT_RELEASE

2. ANATOMICAL_BONES:
- Gaze & head: head level; face pointing forward. Eyes on the rim.
- Torso: trunk line (hips to shoulders) 4 deg forward of vertical; shoulders square with the hips.
- Right arm (shooting arm): upper arm raised 135 deg from the side of the trunk, pointing forward and up; elbow slightly bent (22 deg flexion); forearm pointing up and slightly forward and slightly to the athlete's right; palm facing down and to the athlete's left; wrist flexed 65 deg; hand: relaxed, fingers softly curled; fingertips 2.41 m above the floor.
- Left arm (guide hand, off the ball): upper arm raised 120 deg from the side of the trunk, pointing to the athlete's left and forward and slightly up; elbow bent (45 deg flexion); forearm pointing up; palm facing to the athlete's right and slightly forward; wrist extended (cocked back) 10 deg; hand: open with fingers spread; fingertips 2.49 m above the floor.
- Right leg: hip flexed 8 deg; knee slightly bent (14 deg flexion); thigh pointing down, shin pointing down; ankle plantar-flexed (toes pointed) 40 deg; foot 20 cm above the floor.
- Left leg: hip flexed 6 deg; knee slightly bent (16 deg flexion); thigh pointing down, shin pointing down; ankle plantar-flexed (toes pointed) 40 deg; foot 20 cm above the floor.
- Airborne: lowest point of the body 20 cm above the floor; neither foot touches the ground.
- Technique cue: high release at or just before the top of the jump
- Technique cue: gooseneck follow-through, fingers toward the hoop
- Technique cue: guide hand stays up and quiet
- Technique cue: land in the same spot

3. OBJECT_INTERACTION:
- ball (24 cm diameter): center 2.51 m above the floor; surface 4 cm from the right fingertip (forward and up of it).
- Rim 3.05 m high, 480 cm ahead; the ball has just left the fingertips on a high arc (release angle about 50-55 deg).
- Legal under the FIBA rules: no body contact with an opponent outside the player's own cylinder; the ball has left the hands while both feet are still in the air; no other player touches the ball on its downward flight above the ring; jersey tucked into the shorts.

4. CINEMATIC_CAMERA:
- front_low: low-angle shot looking up, from the front (target side), 85mm short telephoto lens, full-body shot. Defender's-eye view from in front, arm and gooseneck wrist sharp.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Profile: extended arm, flexed wrist, ball arcing up.
- baseline_wide: eye-level shot, three-quarter front view, 28mm wide-angle lens, full-body shot. Wide from the baseline, rim in frame, crowd blurred.

5. KINETIC_ENERGY:
- ball spinning backward off the fingertips, seams blurred
- jersey lifted slightly by the jump
- shadow of the shooter small on the court below
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a basketball player releasing a right-handed jump shot at the top of the jump. Airborne with legs straight and toes pointed down; body upright; right shooting arm extended high and forward toward the rim, elbow almost straight; wrist snapped down in a gooseneck, fingers pointing at the rim; ball just off the fingertips; left guide hand still up beside the head, palm facing sideways, not pushing. High release at or just before the top of the jump. Gooseneck follow-through, fingers toward the hoop. Guide hand stays up and quiet. Land in the same spot. Low-angle shot looking up, from the front (target side), 85mm short telephoto lens, full-body shot. Defender's-eye view from in front, arm and gooseneck wrist sharp. Ball spinning backward off the fingertips, seams blurred; jersey lifted slightly by the jump. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, wrist bent back at release, fingers glued together, ball stuck to the hand, guide hand turned over pushing, body drifting far sideways, feet crossed in the air, shooter landing while still holding the ball, untucked jersey, headband wider than 10 cm
```

## Control images

- `openpose_front_low.png` / `.json`: 896x1152, low-angle shot looking up, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_side.png` / `.json`: 896x1152, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_baseline_wide.png` / `.json`: 1344x768, eye-level shot, three-quarter front view, 28mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_elbow_flex | 22.0 | ..45 | arm nearly extended at release (about 45 deg at release, extending into the follow-through) | S1 |
| r_shoulder_elev | 135.0 | 100.. | shoulder flexion about 103-114 deg at release | S2 |
| r_arm.wrist | 65.0 | 40.. | wrist snapped forward (gooseneck), fingers toward the rim | S3 |
| r_knee_flex | 14.0 | ..25 | legs extended, knee about 13-16 deg at release | S1 |
| r_hand_z | 2.4 | 2.35.. | high release: hand height about 1.28-1.40 x body height | S4 |
| lowest_z | 0.2 | 0.1.. | released near the top of the jump | S5 |

## Official game rules (FIBA Official Basketball Rules 2024 and FIBA Basketball Equipment (OBR 2026 takes effect on 1 October 2026: free line colours, visible-sock rule removed, unsportsmanlike foul renamed; article numbers may move))

| rule | what | check on this skeleton |
|---|---|---|
| FIBA Art. 33.1, 33.2 | Cylinder and verticality: Each player owns the vertical space above their position; a player who leaves their cylinder and makes contact is responsible for it. | text only |
| FIBA Art. 25.2 | Travelling on a shot: A player may jump off the pivot foot to shoot, but the ball must be released before either foot returns to the floor. | OK: ball is 2 cm from the shooting hand |
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

- [S1] Irawan & Prastiwi 2022, JPES: knee 167 deg and elbow 135 deg inside angles at release (convention assumed) http://www.efsupit.ro/images/stories/decembrie2022/Art%20379.pdf
- [S2] Vencurik et al. 2021, IJERPH 18:934: shoulder 103-114 deg at release, elite U16/U18 https://doi.org/10.3390/ijerph18030934
- [S3] Coach's Clipboard / FIBA WABC 2.7.5: wrist flick, gooseneck follow-through https://www.coachesclipboard.net/Shooting.html
- [S4] Cabarkapa et al. 2022: release hand height / body height 1.40 (proficient) vs 1.28 https://doi.org/10.3390/sports10010002
- [S5] Okazaki & Rodacki 2012, JSSM 11:231: release height 2.33-2.46 m, release near the jump peak https://www.jssm.org/jssm-11-231.xml-Fulltext
