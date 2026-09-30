# SOCCER_INSTEP_KICK_BACKSWING

Right-footed soccer instep kick at support-foot plant: left foot planted beside the ball, kicking hip extended and knee folded behind, left arm out wide.

- 이름(ko): 축구 인스텝 킥 백스윙, 슈팅 디딤발, 강슛 준비 동작, 축구 킥 테이크백
- names (en): soccer instep kick backswing, shot plant foot, kicking leg cocked, power shot wind-up

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #SOCCER_INSTEP_KICK_BACKSWING

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 56 deg; face pointing down and slightly forward and slightly to the athlete's right. Head down and still, eyes on the ball.
- Torso: trunk line (hips to shoulders) 3 deg backward of vertical, leaning 16 deg to the athlete's left; spine arched back (extended) 8 deg over the pelvis; shoulder line rotated 18 deg to the left of the hip line (hip-shoulder separation).
- Right arm (swings forward across the body): upper arm raised 45 deg from the side of the trunk, pointing down and forward; elbow deeply bent (70 deg flexion); forearm pointing forward and slightly up and slightly to the athlete's left; palm facing to the athlete's left and down; wrist neutral; hand: relaxed, fingers softly curled; fingertips 1.37 m above the floor.
- Left arm (balance arm, out wide): upper arm raised 85 deg from the side of the trunk, pointing to the athlete's left and slightly backward and slightly down; elbow slightly bent (25 deg flexion); forearm pointing to the athlete's left and slightly down; palm facing backward; wrist neutral; hand: open with fingers spread; fingertips 1.04 m above the floor.
- Right leg (kicking leg): hip extended 28 deg, abducted 12 deg; knee bent to about a right angle (95 deg flexion); thigh pointing down and slightly backward and slightly to the athlete's right, shin pointing backward and up; ankle plantar-flexed (toes pointed) 55 deg; foot 88 cm above the floor.
- Left leg (support leg): hip flexed 30 deg; knee slightly bent (26 deg flexion); thigh pointing down and slightly forward, shin pointing down; ankle neutral; foot flat on the floor.
- Base: ankles 79 cm apart (44% of body height, 1.9x shoulder width); every support foot touches the floor, none floats.
- Technique cue: plant the support foot beside the ball, not behind it
- Technique cue: kicking knee folds tight, heel toward the buttock
- Technique cue: non-kicking arm out wide builds a tension arc across the trunk
- Technique cue: approach from about 30-45 degrees to the target line

3. OBJECT_INTERACTION:
- ball (22 cm diameter): center 0.11 m above the floor; surface 19 cm from the left ankle (to the athlete's right and slightly forward of it).
- Legal under the IFAB rules: the ball touches no arm or hand (the arm starts at the bottom of the armpit); no opponent's head is near the raised boot; no jewellery.

4. CINEMATIC_CAMERA:
- side_low: eye-level shot, side profile view, 35mm standard lens, full-body shot. Ground-level side view: the folded kicking leg and the planted foot beside the ball both read clearly.
- front_three_quarter: low-angle shot looking up, three-quarter front view, 50mm standard lens, full-body shot. Goalkeeper-side three-quarter view, ball in the foreground, sharp focus on the ball.
- ground_wide: camera 0.2 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot. Camera almost on the turf behind the kicker, goal visible in the distance.

5. KINETIC_ENERGY:
- turf and grass blades kicked up behind the plant foot
- motion blur on the kicking foot swinging back
- shirt twisting with the trunk rotation
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a soccer player winding up a right-footed instep shot, left support foot just planted beside the ball. Left foot planted flat beside the ball, about 30 cm to its left and level with it, left knee slightly bent; right kicking leg drawn back behind the body with the hip extended and the knee folded so the heel rises toward the buttock, toes pointed; trunk leaning slightly back and away; left arm stretched out wide and back for balance, right arm swinging forward across the body. Plant the support foot beside the ball, not behind it. Kicking knee folds tight, heel toward the buttock. Non-kicking arm out wide builds a tension arc across the trunk. Approach from about 30-45 degrees to the target line. Eye-level shot, side profile view, 35mm standard lens, full-body shot. Ground-level side view: the folded kicking leg and the planted foot beside the ball both read clearly. Turf and grass blades kicked up behind the plant foot; motion blur on the kicking foot swinging back. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, support foot floating or on tiptoe, support foot directly behind the ball, kicking leg swung forward, both arms hanging at the sides, knee bent backwards, left and right legs swapped, ball touching the arm or hand of the outfield player, boot swinging at an opponent's head, necklace, earrings, bracelet, wristwatch
```

## Control images

- `openpose_side_low.png` / `.json`: 1152x896, eye-level shot, side profile view, 35mm standard lens, full-body shot.
- `openpose_front_three_quarter.png` / `.json`: 896x1152, low-angle shot looking up, three-quarter front view, 50mm standard lens, full-body shot.
- `openpose_ground_wide.png` / `.json`: 1344x768, camera 0.2 m above the floor, ground-level low angle looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_leg.flex | -28.0 | -35..-20 | kicking hip extended up to about 29 deg at the end of the backswing | S1 |
| r_knee_flex | 95.0 | 85..115 | kicking knee near maximum flexion (about 93 deg in elite adults) | S2 |
| l_knee_flex | 26.0 | 18..35 | support knee about 26 deg flexion at plant | S3 |
| left:left_ankle:ball | 30.0 | 20..38 | support foot 27-37 cm beside the ball (best ball speed and accuracy) | S4 |
| fwd:left_ankle:ball | -2.0 | -12..8 | support foot level with or slightly behind the ball centre | S4, S5 |
| l_foot_z | 0.0 | ..0.03 | support foot planted flat | S3 |
| l_shoulder_elev | 85.0 | 60.. | non-kicking arm abducted and extended (tension arc) | S6 |

## Official game rules (IFAB Laws of the Game 2026/27 (dimensions and fouls unchanged from 2025/26))

| rule | what | check on this skeleton |
|---|---|---|
| IFAB Law 12 | Handball: Touching the ball deliberately with the hand/arm, or with a hand/arm that has made the body unnaturally bigger, is an offence; the arm starts at the bottom of the armpit. | OK: ball is 98 cm from the arms and hands |
| IFAB Law 12 | Playing in a dangerous manner: An action that threatens injury while playing the ball (for example a high foot near an opponent's head) is an offence; a scissors or bicycle kick is allowed if it is not dangerous to an opponent. | text only |
| IFAB Law 4 | Jewellery: All jewellery is forbidden and must be removed; covering it with tape is not permitted. | text only |
| equipment | ball_size | OK: diameter_m 0.22 (official 0.2164-0.2229, IFAB Law 2 (68-70 cm around)) |

Scene rules for a full match shot (players, uniforms, officials):

- At most eleven players per team on the field, one of them the goalkeeper. (IFAB Law 3)
- Each goalkeeper wears colours clearly different from all other players and the match officials. (IFAB Law 4)
- Players wear a shirt with sleeves, shorts, socks covering the shinguards, and boots; any tape on the socks matches the sock colour. (IFAB Law 4)
- No jewellery of any kind (necklaces, rings, bracelets, earrings, leather or rubber bands), not even taped over. (IFAB Law 4)
- The referee on the field with two assistant referees with flags along the touchlines, level with the second-last defender; a fourth official between the technical areas. (IFAB Law 6, practical guidelines)
- White lines at most 12 cm wide; goal 7.32 m between the posts and 2.44 m under the crossbar; penalty area 16.5 m deep, penalty mark 11 m from the goal line; corner flags at least 1.5 m high. (IFAB Law 1)

Rulebook: https://www.theifab.com/laws/latest/

## Sources

- [S1] Kellis & Katis 2007, JSSM 6:154, biomechanics of the soccer kick (hip extension up to 29 deg in the backswing) https://www.jssm.org/hf.php?id=jssm-06-154.xml
- [S2] Systematic review of instep-kick kinematics in elite adult players (maximum knee flexion 93 +/- 5 deg) https://drantoniopetrolo.ca/wp-content/uploads/2024/01/KINEMATIC-DETERMINANTS-OF-THE-INSTEP-SOCCER-KICK-IN-ELITE-ADULT-SOCCER-PLAYERS_A-SYSTEMATIC-REVIEW.pdf
- [S3] Lees et al. 2010, J Sports Sci review: support knee 26 deg at plant, 42 deg at contact; pelvis rotates 30-36 deg to contact https://pubmed.ncbi.nlm.nih.gov/20509089/
- [S4] Ou, Lei & Cheng, Science and Medicine in Football 7:34-40: support foot beside or slightly ahead of the ball, 27-37 cm to the side https://www.tandfonline.com/doi/full/10.1080/24733938.2022.2055781
- [S5] McLean & Tumilty 1993 via Basumatary thesis: support foot about 30 cm to the side and 5-10 cm behind https://vuir.vu.edu.au/15563/
- [S6] Shan & Westerhoff 2005, Sports Biomech 4:59-72: full-body tension arc of the maximal instep kick https://www.researchgate.net/publication/7929595
