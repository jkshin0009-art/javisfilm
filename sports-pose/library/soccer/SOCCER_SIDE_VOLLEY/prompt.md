# SOCCER_SIDE_VOLLEY

Right-footed soccer side volley at contact: kicking leg swung round near horizontal at hip height, trunk leaning far away from the ball, both arms raised for balance.

- 이름(ko): 축구 사이드 발리, 발리슛, 논스톱 발리, 옆으로 누운 발리
- names (en): soccer side volley, volley shot, first-time volley, side-on volley

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #SOCCER_SIDE_VOLLEY

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 45 deg, turned 27 deg to the athlete's right of the chest line; face pointing to the athlete's right and forward and slightly down. Eyes on the ball at contact.
- Torso: trunk line (hips to shoulders) 5 deg forward of vertical, leaning 48 deg to the athlete's left; shoulder line rotated 30 deg to the left of the hip line (hip-shoulder separation).
- Right arm (balance arm, high side): upper arm raised 110 deg from the side of the trunk, pointing up and forward and slightly to the athlete's right; elbow slightly bent (30 deg flexion); forearm pointing forward and slightly up; palm facing to the athlete's right; wrist neutral; hand: open with fingers spread; fingertips 1.88 m above the floor.
- Left arm (balance arm, low side): upper arm raised 75 deg from the side of the trunk, pointing down and slightly to the athlete's left; elbow slightly bent (25 deg flexion); forearm pointing down and forward and slightly to the athlete's left; palm facing down and backward and slightly to the athlete's right; wrist neutral; hand: open with fingers spread; fingertips 0.52 m above the floor.
- Right leg (kicking leg): hip flexed 80 deg, abducted 61 deg; knee deeply bent (72 deg flexion); thigh pointing to the athlete's right and slightly forward and slightly up, shin pointing down and forward; ankle plantar-flexed (toes pointed) 40 deg; foot 70 cm above the floor.
- Left leg (support leg): hip flexed 22 deg; knee bent (32 deg flexion); thigh pointing down and slightly forward, shin pointing down and slightly to the athlete's right; ankle dorsiflexed 14 deg; foot flat on the floor.
- Base: ankles 59 cm apart (33% of body height, 1.5x shoulder width); every support foot touches the floor, none floats.
- Technique cue: lean the trunk away from the ball
- Technique cue: swing the kicking leg round with the hip turned in
- Technique cue: keep the foot flat over the top of the ball to keep the shot down
- Technique cue: both arms up for balance

3. OBJECT_INTERACTION:
- ball (22 cm diameter): center 0.86 m above the floor; touching the right instep; surface 64 cm from the right hip (to the athlete's right and slightly forward of it).

4. CINEMATIC_CAMERA:
- front: eye-level shot, from the front (target side), 50mm standard lens, full-body shot. From the goal: the horizontal kicking leg and the leaning trunk form a clear line.
- low_three_quarter: camera 0.4 m above the floor, ground-level low angle looking up, three-quarter front view, 35mm standard lens, full-body shot. Low three-quarter view from the ball side, ball in sharp focus.
- wide_cinema: eye-level shot, three-quarter front view, 24mm wide-angle lens, full-body shot. Wide frame, penalty box lines and crowd behind.

5. KINETIC_ENERGY:
- ball flattening against the laces
- grass flying off the support boot
- shirt and shorts pulled by the rotation, motion blur on the kicking leg
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a soccer player hitting a right-footed side volley, the ball met at hip height beside the body. Left support foot planted, left knee bent; trunk leaning far to the left, away from the ball; right kicking leg swung round and raised near horizontal, knee slightly bent, foot flat and turned over the top of the ball with the toes pointed; both arms raised out to the sides for balance; hips turning toward the goal. Lean the trunk away from the ball. Swing the kicking leg round with the hip turned in. Keep the foot flat over the top of the ball to keep the shot down. Both arms up for balance. Eye-level shot, from the front (target side), 50mm standard lens, full-body shot. From the goal: the horizontal kicking leg and the leaning trunk form a clear line. Ball flattening against the laces; grass flying off the support boot. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, upright trunk, kicking leg drawn as a front kick, support leg straight and locked, arms at the sides, ball far below the foot, hip joint twisted impossibly
```

## Control images

- `openpose_front.png` / `.json`: 1152x896, eye-level shot, from the front (target side), 50mm standard lens, full-body shot.
- `openpose_low_three_quarter.png` / `.json`: 1152x896, camera 0.4 m above the floor, ground-level low angle looking up, three-quarter front view, 35mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, eye-level shot, three-quarter front view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: r_leg.abd = 61 is beyond the usual range -25..50

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| trunk_lean_right | -48.1 | ..-25 | trunk leans far away from the ball; lean grows with ball height | S1, S2 |
| r_shoulder_elev | 110.0 | 70.. | arms raised near horizontal for balance (abduction over 80 deg in jumping volleys) | S3 |
| l_shoulder_elev | 75.0 | 55.. | arms raised for balance | S3 |
| z:ball | 0.9 | 0.55..1.05 | ball met between knee and waist height | S1, S4 |
| l_foot_z | 0.0 | ..0.03 | support foot planted | S1 |
| l_knee_flex | 32.0 | 15..50 | support knee flexed | S1 |

## Sources

- [S1] Sugi, Nunome, Tamura & Iga, ISBS 2017: volley vs instep kick (more knee flexion, trunk lean and pelvis rotation) - search extract https://commons.nmu.edu/isbs/vol35/iss1/41/
- [S2] Shan & Zhang 2011 / Shan 2022: trunk side lean and pelvis twist increase with ball height https://link.springer.com/article/10.1186/1758-2555-3-23
- [S3] Shan et al. 2020, Applied Sciences 10:4785: jumping side volley, trunk twist about 40 deg, shoulder abduction over 80 deg https://www.mdpi.com/2076-3417/10/14/4785
- [S4] ISBS 2020: successful vs failed volleys (foot over the top of the ball keeps the shot down) https://commons.nmu.edu/isbs/vol38/iss1/151/
