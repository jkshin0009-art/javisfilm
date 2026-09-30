# VOLLEYBALL_OVERHEAD_SET

Volleyball overhead set (setter's pass) at contact: ball just above and in front of the forehead, both hands shaped around it with the thumbs toward the eyes.

- 이름(ko): 배구 토스, 오버핸드 패스, 세터 토스, 배구 세트
- names (en): volleyball set, overhead pass, setter hands, front set

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #VOLLEYBALL_OVERHEAD_SET

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 59 deg; face pointing up and forward. Eyes up on the ball through the triangle of the hands.
- Torso: trunk line (hips to shoulders) 4 deg forward of vertical; shoulders square with the hips.
- Right arm: upper arm raised 153 deg from the side of the trunk, pointing up and slightly forward and slightly to the athlete's right; elbow bent to about a right angle (85 deg flexion); forearm pointing to the athlete's left and slightly up and slightly backward; palm facing forward and to the athlete's left; wrist extended (cocked back) 9 deg; hand: cupped, fingers slightly curled and spread; fingertips 2.06 m above the floor.
- Left arm: upper arm raised 153 deg from the side of the trunk, pointing up and slightly forward and slightly to the athlete's left; elbow bent to about a right angle (85 deg flexion); forearm pointing to the athlete's right and slightly up and slightly backward; palm facing forward and to the athlete's right; wrist extended (cocked back) 9 deg; hand: cupped, fingers slightly curled and spread; fingertips 2.06 m above the floor.
- Right leg (slightly forward): hip flexed 32 deg; knee bent (38 deg flexion); thigh pointing down and slightly forward, shin pointing down; ankle dorsiflexed 13 deg; foot flat on the floor.
- Left leg: hip flexed 20 deg; knee bent (30 deg flexion); thigh pointing down, shin pointing down and slightly backward; ankle dorsiflexed 17 deg; foot flat on the floor.
- Base: ankles 39 cm apart (21% of body height, 0.9x shoulder width); every support foot touches the floor, none floats.
- Technique cue: all ten fingers on the ball
- Technique cue: thumbs point back toward the eyes, thumbs not touching
- Technique cue: contact just in front of the hairline, not over the skull
- Technique cue: elbows slightly forward and out

3. OBJECT_INTERACTION:
- ball (21 cm diameter): center 2.00 m above the floor; surface 14 cm from the forehead (up and forward of it).

4. CINEMATIC_CAMERA:
- front: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. Hands and the triangle window around the ball in sharp focus.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Profile shows the ball above the forehead and the bent elbows.
- low_three_quarter: low-angle shot looking up, three-quarter front view, 35mm standard lens, full-body shot. Low angle looking up at the ball in the setter's hands, arena lights above.

5. KINETIC_ENERGY:
- ball leaving the fingertips with a clean arc, no spin
- fingers flexing slightly on contact
- knees and arms extending together
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a volleyball setter setting the ball with both hands just above the forehead. Feet shoulder-width, right foot slightly forward, knees slightly bent; ball just above and in front of the forehead; both hands shaped around the back of the ball, fingers spread, thumbs pointing back toward the eyes, thumbs and index fingers forming a triangle window; elbows bent and slightly out. All ten fingers on the ball. Thumbs point back toward the eyes, thumbs not touching. Contact just in front of the hairline, not over the skull. Elbows slightly forward and out. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. Hands and the triangle window around the ball in sharp focus. Ball leaving the fingertips with a clean arc, no spin; fingers flexing slightly on contact. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, hands at the chest, palms slapping the ball, crossed thumbs, ball floating far from the fingers, ball behind the head
```

## Control images

- `openpose_front.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_side.png` / `.json`: 896x1152, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_low_three_quarter.png` / `.json`: 896x1152, low-angle shot looking up, three-quarter front view, 35mm standard lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| up:ball:forehead | 20.0 | 10..32 | ball contacted just above the forehead (5-8 cm in front of the hairline) | S1 |
| fwd:ball:forehead | 14.0 | 5..25 | ball in front of the forehead, not over the skull | S1 |
| r_elbow_flex | 85.2 | 60..110 | elbows bent, slightly forward and out | S1, S2 |
| l_elbow_flex | 85.2 | 60..110 | elbows bent, slightly forward and out | S1, S2 |
| r_knee_flex | 38.0 | 15..50 | knees slightly bent | S1 |
| dist:r_palm:l_palm | 11.8 | 10..26 | hands on both sides of the ball, thumbs not touching | S1 |

## Sources

- [S1] Human Kinetics excerpt on overhead passing and Volleyball Magazine setting fundamentals (triangle window, contact 5-8 cm in front of the hairline, elbows forward and out) https://us.humankinetics.com/blogs/excerpt/overhead-passing
- [S2] MDPI Biomechanics 2022: setter kinematics, professional vs non-professional (knee, shoulder flexion) https://www.mdpi.com/2673-7078/2/4/42
