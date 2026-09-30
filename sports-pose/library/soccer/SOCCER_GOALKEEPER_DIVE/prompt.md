# SOCCER_GOALKEEPER_DIVE

Soccer goalkeeper diving to the right at full stretch: body horizontal and side-on to the shooter, both arms reaching past the head, hands spread on the ball.

- 이름(ko): 골키퍼 다이빙, 골키퍼 선방, 다이빙 세이브, 키퍼 몸 날리기
- names (en): goalkeeper dive, diving save, full-stretch save, keeper dive to the right

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #SOCCER_GOALKEEPER_DIVE

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 75 deg, turned 25 deg to the athlete's left of the chest line; face pointing to the athlete's right and slightly up. Eyes locked on the ball between the gloves.
- Torso: trunk line (hips to shoulders) 58 deg forward of vertical, leaning 85 deg to the athlete's right; spine flexed 8 deg over the pelvis; shoulder line rotated 13 deg to the left of the hip line (hip-shoulder separation).
- Right arm (lower hand, behind the ball): upper arm raised 180 deg from the side of the trunk, pointing to the athlete's right; elbow bent (35 deg flexion); forearm pointing to the athlete's right and slightly up and slightly backward; palm facing up and slightly to the athlete's left and slightly backward; wrist extended (cocked back) 19 deg; hand: open with fingers spread; fingertips 0.86 m above the floor.
- Left arm (top hand): upper arm raised 180 deg from the side of the trunk, pointing to the athlete's right; elbow bent (35 deg flexion); forearm pointing to the athlete's right and backward; palm facing down; wrist flexed 5 deg; hand: open with fingers spread; fingertips 1.07 m above the floor.
- Right leg (lower leg): hip flexed 10 deg; knee slightly bent (20 deg flexion); thigh pointing to the athlete's left and slightly down, shin pointing to the athlete's left and slightly down; ankle plantar-flexed (toes pointed) 30 deg; foot 35 cm above the floor.
- Left leg (push-off leg, trailing): hip flexed 30 deg; knee bent (55 deg flexion); thigh pointing to the athlete's left and slightly forward, shin pointing to the athlete's left and slightly backward; ankle plantar-flexed (toes pointed) 35 deg; foot 81 cm above the floor.
- Airborne: lowest point of the body 35 cm above the floor; neither foot touches the ground.
- Technique cue: push off from the near-side leg
- Technique cue: body side-on, not facing the ground
- Technique cue: hands lead, fingers spread behind and on top of the ball
- Technique cue: head stays in line and watches the ball into the hands

3. OBJECT_INTERACTION:
- ball (22 cm diameter): center 0.95 m above the floor; surface 32 cm from the crown (to the athlete's right of it).
- Goal 7.32 m wide and 2.44 m high, goal line about 1 m behind the keeper; the save is inside the penalty area.
- Legal under the IFAB rules: the goalkeeper handles the ball inside their own penalty area; the goalkeeper wears a kit colour different from both teams and the referee; no jewellery.

4. CINEMATIC_CAMERA:
- shooter_view: eye-level shot, from the front (target side), 50mm standard lens, full-body shot. From the penalty spot: the keeper stretched horizontally across the frame, goal net behind.
- behind_goal: eye-level shot, from behind, 35mm standard lens, full-body shot. From behind the net, mesh soft in the foreground, sharp focus on the gloves.
- low_side: camera 0.3 m above the floor, ground-level low angle looking up, three-quarter front view, 28mm wide-angle lens, full-body shot. Low angle from the turf, keeper flying above the grass.

5. KINETIC_ENERGY:
- body frozen mid-flight above the turf
- grass and water spray thrown up by the push-off
- ball spinning into the gloves, motion blur on the ball's path
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a soccer goalkeeper diving to the right at full stretch to save a shot. Body airborne and nearly horizontal, lying on its right side, chest facing the shooter; both arms straight and reaching past the head toward the ball, lower hand behind the ball and top hand over it, gloves open with fingers spread; left push-off leg trailing with the knee bent, right leg extended below; head in line with the arms. Push off from the near-side leg. Body side-on, not facing the ground. Hands lead, fingers spread behind and on top of the ball. Head stays in line and watches the ball into the hands. Eye-level shot, from the front (target side), 50mm standard lens, full-body shot. From the penalty spot: the keeper stretched horizontally across the frame, goal net behind. Body frozen mid-flight above the turf; grass and water spray thrown up by the push-off. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, no gloves, extra or fused fingers, body facing the camera flat, legs in a running pose, ball stuck inside the hands, keeper touching the ground, goalkeeper handling the ball far outside the penalty area, goalkeeper in the same colour as the outfield players, necklace, earrings, bracelet, wristwatch
```

## Control images

- `openpose_shooter_view.png` / `.json`: 1344x768, eye-level shot, from the front (target side), 50mm standard lens, full-body shot.
- `openpose_behind_goal.png` / `.json`: 1344x768, eye-level shot, from behind, 35mm standard lens, full-body shot.
- `openpose_low_side.png` / `.json`: 1344x768, camera 0.3 m above the floor, ground-level low angle looking up, three-quarter front view, 28mm wide-angle lens, full-body shot.

## Checks

- warn: head.flex = -75 is beyond the usual range -65..56
- warn: r_arm.rot = -74 is beyond the usual range -70..120

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| lowest_z | 0.4 | 0.2.. | airborne at full stretch | S1 (general coaching cue) |
| r_elbow_flex | 35.0 | ..35 | arms reaching out, nearly straight | S1 |
| r_shoulder_elev | 180.0 | 140.. | both arms reaching past the head toward the ball | S1 |
| trunk_from_vertical | 84.8 | 55.. | body close to horizontal, side-on to the shooter | S1 |

## Official game rules (IFAB Laws of the Game 2026/27 (dimensions and fouls unchanged from 2025/26))

| rule | what | check on this skeleton |
|---|---|---|
| IFAB Law 12 | Goalkeeper handling outside the penalty area: The goalkeeper may handle the ball only inside their own penalty area; outside it the goalkeeper has the same handling restrictions as any other player. | OK: inside |
| IFAB Law 4 | Goalkeeper colours: The goalkeeper's kit must be distinguishable from the other players and the match officials. | text only |
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

- [S1] General goalkeeper diving cues (push off the near leg, side-on body, hands lead); kinematics: Sci Rep 2024 penalty dive study (values not retrieved) https://www.nature.com/articles/s41598-024-60074-x
