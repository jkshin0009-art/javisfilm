# VOLLEYBALL_FOREARM_PASS

Volleyball forearm pass (bump / serve receive) at contact: wide stance, knees bent, straight arms joined into a flat platform, ball on the forearms just above the wrists.

- 이름(ko): 배구 리시브, 언더핸드 패스, 배구 범프, 서브 리시브, 리시브 자세
- names (en): volleyball forearm pass, bump pass, serve receive, dig platform, underhand pass

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #VOLLEYBALL_FOREARM_PASS

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 15 deg; face pointing down and slightly forward. Eyes on the ball at contact, chin slightly down.
- Torso: trunk line (hips to shoulders) 42 deg forward of vertical; spine flexed 12 deg over the pelvis; shoulders square with the hips.
- Right arm (platform): upper arm raised 54 deg from the side of the trunk, pointing down and slightly to the athlete's left; elbow straight (0 deg flexion); forearm pointing down and slightly to the athlete's left; palm facing forward and slightly up and slightly to the athlete's left; wrist flexed 10 deg; hand: clasped with the other hand, thumbs parallel; fingertips 0.45 m above the floor.
- Left arm (platform): upper arm raised 54 deg from the side of the trunk, pointing down and slightly to the athlete's right; elbow straight (0 deg flexion); forearm pointing down and slightly to the athlete's right; palm facing forward and slightly up and slightly to the athlete's right; wrist flexed 10 deg; hand: clasped with the other hand, thumbs parallel; fingertips 0.45 m above the floor.
- Right leg: hip flexed 62 deg, abducted 24 deg; knee deeply bent (70 deg flexion); thigh pointing down and slightly forward and slightly to the athlete's right, shin pointing down and backward; ankle dorsiflexed 32 deg; foot flat on the floor.
- Left leg (slightly forward): hip flexed 72 deg, abducted 22 deg; knee bent (64 deg flexion); thigh pointing down and forward and slightly to the athlete's left, shin pointing down and slightly backward; ankle dorsiflexed 18 deg; foot flat on the floor.
- Base: ankles 57 cm apart (31% of body height, 1.4x shoulder width); every support foot touches the floor, none floats.
- Technique cue: shoulders rolled forward and over the knees
- Technique cue: flat platform, contact just above the wrists
- Technique cue: arms do not swing above the shoulders
- Technique cue: weight shifting onto the front foot

3. OBJECT_INTERACTION:
- ball (21 cm diameter): center 0.71 m above the floor; surface 5 cm from the hands mid (forward and up of it); surface 43 cm from the right knee (forward and to the athlete's left and slightly up of it).

4. CINEMATIC_CAMERA:
- front_low: eye-level shot, from the front (target side), 50mm standard lens, full-body shot. Seen from the server's side: the flat platform and the bent knees face the camera.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Profile shows the platform angle and the shoulders over the knees.
- three_quarter_high: high-angle shot looking down, three-quarter front view, 35mm standard lens, full-body shot. Broadcast-style high three-quarter view, floor lines visible.

5. KINETIC_ENERGY:
- ball rebounding upward off the forearms with slight spin blur
- sneakers gripping the court, knees absorbing the serve
- red marks forming on the inner forearms
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a volleyball player receiving a serve with a forearm pass, ball contacting the joined forearms. Feet wider than the shoulders and flat on the floor, knees bent about 65 degrees, hips back, trunk leaning forward so the shoulders are over the knees; both arms straight and pressed together in front of the body, hands clasped with thumbs side by side, forming one flat platform angled toward the target; ball on the forearms just above the wrists, between the waist and knee height. Shoulders rolled forward and over the knees. Flat platform, contact just above the wrists. Arms do not swing above the shoulders. Weight shifting onto the front foot. Eye-level shot, from the front (target side), 50mm standard lens, full-body shot. Seen from the server's side: the flat platform and the bent knees face the camera. Ball rebounding upward off the forearms with slight spin blur; sneakers gripping the court, knees absorbing the serve. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, bent elbows, hands apart, ball on the fists or hands, straight locked knees, arms swung above the shoulders
```

## Control images

- `openpose_front_low.png` / `.json`: 1152x896, eye-level shot, from the front (target side), 50mm standard lens, full-body shot.
- `openpose_side.png` / `.json`: 1152x896, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_three_quarter_high.png` / `.json`: 896x1152, high-angle shot looking down, three-quarter front view, 35mm standard lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_elbow_flex | 0.0 | ..12 | arms straight, elbows locked | S1 |
| l_elbow_flex | 0.0 | ..12 | arms straight, elbows locked | S1 |
| dist:r_wrist:l_wrist | 6.7 | ..8 | hands joined into one platform | S1 |
| stance_over_shoulders | 1.4 | 1.1..1.8 | feet slightly wider than the shoulders | S1 |
| r_knee_flex | 70.0 | 45..90 | knees flexed, low body | S1, S2 |
| l_knee_flex | 64.0 | 45..90 | knees flexed, low body | S1, S2 |
| z:ball | 0.7 | 0.55..1.05 | contact between the waist and the knees | S1 |
| trunk_lean_fwd | 42.0 | 25..55 | shoulders over the knees, trunk leaning forward | S1 |

## Sources

- [S1] FIVB Coaches Manual Level II: forearm pass (feet wider than shoulders, shoulders over knees, flat platform, contact just above the wrists) https://www.fivb.com/wp-content/uploads/2024/03/Coaches_Manual_Level_II_EN.pdf
- [S2] Ridgway & Hamilton, ISBS: forearm pass kinematics (thigh about 46 deg at the start, contact about 7 cm from the wrist) https://ojs.ub.uni-konstanz.de/cpa/article/view/2336
