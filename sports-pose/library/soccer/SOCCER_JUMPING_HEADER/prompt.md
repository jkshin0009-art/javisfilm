# SOCCER_JUMPING_HEADER

Soccer jumping header at contact: airborne after a one-foot takeoff, ball on the forehead, trunk snapping forward, elbows out for balance.

- 이름(ko): 축구 점프 헤딩, 헤더, 공중볼 헤딩, 헤딩슛
- names (en): soccer jumping header, header, aerial duel header, headed goal

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #SOCCER_JUMPING_HEADER

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 8 deg; face pointing forward and slightly down. Eyes open and on the ball, mouth closed.
- Torso: trunk line (hips to shoulders) 22 deg forward of vertical; spine flexed 14 deg over the pelvis; shoulders square with the hips.
- Right arm: upper arm raised 75 deg from the side of the trunk, pointing to the athlete's right and slightly down and slightly forward; elbow bent to about a right angle (85 deg flexion); forearm pointing forward and slightly up; palm facing down and slightly forward; wrist neutral; hand: relaxed, fingers softly curled; fingertips 2.00 m above the floor.
- Left arm: upper arm raised 70 deg from the side of the trunk, pointing to the athlete's left and slightly down and slightly forward; elbow bent to about a right angle (90 deg flexion); forearm pointing forward and slightly up; palm facing down and slightly forward; wrist neutral; hand: relaxed, fingers softly curled; fingertips 1.97 m above the floor.
- Right leg (swing leg): hip flexed 45 deg; knee bent to about a right angle (85 deg flexion); thigh pointing down and forward, shin pointing backward and down; ankle plantar-flexed (toes pointed) 30 deg; foot 54 cm above the floor.
- Left leg (takeoff leg): hip flexed 5 deg; knee bent (35 deg flexion); thigh pointing down, shin pointing down and backward; ankle plantar-flexed (toes pointed) 45 deg; foot 40 cm above the floor.
- Airborne: lowest point of the body 40 cm above the floor; neither foot touches the ground.
- Technique cue: contact with the forehead, not the top of the head
- Technique cue: keep head, neck and torso aligned
- Technique cue: arch then snap the trunk forward
- Technique cue: arms out for balance and to hold space

3. OBJECT_INTERACTION:
- ball (22 cm diameter): center 2.06 m above the floor; touching the forehead.

4. CINEMATIC_CAMERA:
- side_low: low-angle shot looking up, side profile view, 50mm standard lens, full-body shot. Profile: forehead meeting the ball, neck and trunk in one line.
- front_low: low-angle shot looking up, from the front (target side), 35mm standard lens, full-body shot. Low angle from in front, sky or stadium roof behind, ball in sharp focus.
- wide_cinema: low-angle shot looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the header toward the goal.

5. KINETIC_ENERGY:
- ball compressing against the forehead, water spray flying off the ball
- hair flicked forward by the impact
- defender's shadow on the grass below
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a soccer player rising for a jumping header, the ball meeting the forehead. Airborne after a one-foot takeoff, left leg hanging nearly straight with toes pointed, right knee bent and lifted; trunk snapping forward from the hips; head, neck and trunk locked in one line; forehead (hairline) meeting the back of the ball; eyes open; both elbows raised out to the sides at shoulder height. Contact with the forehead, not the top of the head. Keep head, neck and torso aligned. Arch then snap the trunk forward. Arms out for balance and to hold space. Low-angle shot looking up, side profile view, 50mm standard lens, full-body shot. Profile: forehead meeting the ball, neck and trunk in one line. Ball compressing against the forehead, water spray flying off the ball; hair flicked forward by the impact. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, ball on the top of the head or the face, eyes shut, head tipped back, feet on the ground, arms merged into another player
```

## Control images

- `openpose_side_low.png` / `.json`: 896x1152, low-angle shot looking up, side profile view, 50mm standard lens, full-body shot.
- `openpose_front_low.png` / `.json`: 896x1152, low-angle shot looking up, from the front (target side), 35mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, low-angle shot looking up, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| lowest_z | 0.4 | 0.25.. | airborne jump header | S1 |
| head.flex | 8.0 | -5..20 | head, neck and trunk aligned, chin not tipped back | S2 |
| trunk.flex | 14.0 | 5.. | trunk snapping forward into the ball | S2 |
| r_shoulder_elev | 75.0 | 45..100 | arms out for balance and space | S3 (general coaching cue) |

## Sources

- [S1] Landing after jump headers, 2024 (knee and hip landing angles) - search extract https://www.sciencedirect.com/science/article/abs/pii/S0968016024001339
- [S2] Shewchenko et al. 2005, BJSM: heading technique, aligned head-neck-torso reduces head acceleration https://biokinetics.com/wp-content/uploads/2024/04/Shewchenko-et-al-2005-Heading-in-Football-Part-2-BJSM.pdf
- [S3] J Hum Kinet: heading in soccer, neck muscle activity in jumping headers https://jhk.termedia.pl/pdf-158515-84803?filename=Heading-in-Soccer--Does-K.pdf
