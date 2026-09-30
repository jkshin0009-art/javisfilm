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
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, wrist bent back at release, fingers glued together, ball stuck to the hand, guide hand turned over pushing, body drifting far sideways, feet crossed in the air
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

## Sources

- [S1] Irawan & Prastiwi 2022, JPES: knee 167 deg and elbow 135 deg inside angles at release (convention assumed) http://www.efsupit.ro/images/stories/decembrie2022/Art%20379.pdf
- [S2] Vencurik et al. 2021, IJERPH 18:934: shoulder 103-114 deg at release, elite U16/U18 https://doi.org/10.3390/ijerph18030934
- [S3] Coach's Clipboard / FIBA WABC 2.7.5: wrist flick, gooseneck follow-through https://www.coachesclipboard.net/Shooting.html
- [S4] Cabarkapa et al. 2022: release hand height / body height 1.40 (proficient) vs 1.28 https://doi.org/10.3390/sports10010002
- [S5] Okazaki & Rodacki 2012, JSSM 11:231: release height 2.33-2.46 m, release near the jump peak https://www.jssm.org/jssm-11-231.xml-Fulltext
