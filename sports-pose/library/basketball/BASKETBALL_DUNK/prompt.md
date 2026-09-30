# BASKETBALL_DUNK

One-hand basketball dunk: airborne with the right arm fully extended, ball above the rim in the right hand, wrist snapping down, left arm out for balance, right knee raised.

- 이름(ko): 농구 덩크, 원핸드 덩크, 슬램덩크, 림 위 덩크
- names (en): basketball dunk, one-hand slam dunk, dunk above the rim, slam

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASKETBALL_DUNK

2. ANATOMICAL_BONES:
- Gaze & head: head level, turned 13 deg to the athlete's right of the chest line; face pointing forward. Eyes on the rim.
- Torso: trunk line (hips to shoulders) 6 deg backward of vertical, leaning 10 deg to the athlete's left; spine arched back (extended) 6 deg over the pelvis; shoulder line rotated 9 deg to the left of the hip line (hip-shoulder separation).
- Right arm (dunking arm): upper arm raised 137 deg from the side of the trunk, pointing up and slightly forward; elbow slightly bent (12 deg flexion); forearm pointing up and slightly forward; palm facing down and slightly forward; wrist flexed 34 deg; hand: fingers spread around the ball, palm not touching it fully; fingertips 3.43 m above the floor.
- Left arm (balance arm): upper arm raised 70 deg from the side of the trunk, pointing to the athlete's left and slightly down and slightly forward; elbow bent (40 deg flexion); forearm pointing forward and to the athlete's left; palm facing down; wrist neutral; hand: open with fingers spread; fingertips 2.47 m above the floor.
- Right leg (knee raised): hip flexed 70 deg; knee bent to about a right angle (95 deg flexion); thigh pointing forward and slightly down, shin pointing down and slightly backward; ankle plantar-flexed (toes pointed) 30 deg; foot 131 cm above the floor.
- Left leg: hip flexed 10 deg; knee bent (40 deg flexion); thigh pointing down, shin pointing down and slightly backward; ankle plantar-flexed (toes pointed) 40 deg; foot 100 cm above the floor.
- Airborne: lowest point of the body 100 cm above the floor; neither foot touches the ground.
- Technique cue: hand above the rim, fingers spread over the ball
- Technique cue: free arm out for balance
- Technique cue: rim at about 1.6 times the player's height

3. OBJECT_INTERACTION:
- ball (24 cm diameter): center 3.23 m above the floor; surface 10 cm from the rim (up and slightly backward of it).
- Rim 3.05 m high (inner diameter 45 cm, about twice the ball); ball 18 cm above the rim, fingertips 38 cm above it; backboard behind the rim.

4. CINEMATIC_CAMERA:
- under_rim: extreme low-angle shot looking up, three-quarter front view, 24mm wide-angle lens, full-body shot. From below the rim looking up, backboard and arena lights behind, extreme perspective.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Profile: the arm above the rim and the raised knee.
- wide_cinema: eye-level shot, three-quarter rear view, 28mm wide-angle lens, full-body shot. Wide cinematic frame from the key, crowd rising behind.

5. KINETIC_ENERGY:
- net starting to whip upward
- rim flexing under the hand
- camera flashes in the crowd, sweat flying
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a basketball player throwing down a one-hand dunk, ball above the rim. Airborne high above the floor; right arm fully extended overhead, ball palmed in the right hand just above the rim, wrist flexing to push it down through the hoop; left arm out to the side for balance; right knee raised, left leg hanging with toes pointed; trunk slightly arched. Hand above the rim, fingers spread over the ball. Free arm out for balance. Rim at about 1.6 times the player's height. Extreme low-angle shot looking up, three-quarter front view, 24mm wide-angle lens, full-body shot. From below the rim looking up, backboard and arena lights behind, extreme perspective. Net starting to whip upward; rim flexing under the hand. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, ball too big or small for the rim, hand passing through the rim, rim at the wrong height for the player, missing net or backboard, fingers merged with the ball, both arms mirrored
```

## Control images

- `openpose_under_rim.png` / `.json`: 896x1152, extreme low-angle shot looking up, three-quarter front view, 24mm wide-angle lens, full-body shot.
- `openpose_side.png` / `.json`: 896x1152, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, eye-level shot, three-quarter rear view, 28mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| up:r_fingertip:rim | 37.6 | 10.. | hand clearly above the rim (dunk contestants reach about 55 cm above it) | S1 |
| up:ball:rim | 18.0 | 5.. | ball above the rim before being thrown down | S1 |
| r_elbow_flex | 11.8 | ..30 | dunking arm extended (estimate from technique descriptions) | S1 |
| lowest_z | 1.0 | 0.5.. | high vertical jump (about 0.8-1.0 m in dunkers) | S1 |

## Sources

- [S1] Tong & Wang 2024, PLoS ONE: NBA dunk contest participants, standing reach 258-268 cm, max vertical 95-102 cm https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0299262
