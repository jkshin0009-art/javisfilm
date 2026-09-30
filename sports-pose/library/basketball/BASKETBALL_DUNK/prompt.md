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
- Legal under the FIBA rules: no body contact with an opponent outside the player's own cylinder; the hand pushes the ball down through the ring and grasps the ring at most momentarily; jersey tucked into the shorts.

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
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, ball too big or small for the rim, hand passing through the rim, rim at the wrong height for the player, missing net or backboard, fingers merged with the ball, both arms mirrored, player hanging from the ring with full body weight, untucked jersey, headband wider than 10 cm
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

## Official game rules (FIBA Official Basketball Rules 2024 and FIBA Basketball Equipment (OBR 2026 takes effect on 1 October 2026: free line colours, visible-sock rule removed, unsportsmanlike foul renamed; article numbers may move))

| rule | what | check on this skeleton |
|---|---|---|
| FIBA Art. 33.1, 33.2 | Cylinder and verticality: Each player owns the vertical space above their position; a player who leaves their cylinder and makes contact is responsible for it. | text only |
| FIBA Art. 33.6 | Landing space: A player who has jumped has the right to land at the same place (or at a spot not occupied by an opponent at take-off). | text only |
| FIBA Art. 36 (technical foul) | Hanging on the ring: Hanging so that the ring supports the player's weight is a technical foul; after a dunk the ring may be grasped only momentarily, or to prevent injury. | text only |
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

- [S1] Tong & Wang 2024, PLoS ONE: NBA dunk contest participants, standing reach 258-268 cm, max vertical 95-102 cm https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0299262
