# VOLLEYBALL_BLOCK

Volleyball block at the top of the jump: both arms straight and reaching over the net into the opponent's court, hands wide open, shoulders parallel to the net.

- 이름(ko): 배구 블로킹, 블록 점프, 네트 위 손 뻗기, 블로커
- names (en): volleyball block, blocking jump, hands over the net, blocker

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #VOLLEYBALL_BLOCK

2. ANATOMICAL_BONES:
- Gaze & head: head level; face pointing forward. Eyes on the attacker's hitting arm across the net.
- Torso: trunk line (hips to shoulders) 14 deg forward of vertical; spine flexed 8 deg over the pelvis; shoulders square with the hips.
- Right arm: upper arm raised 161 deg from the side of the trunk, pointing up and slightly forward; elbow slightly bent (15 deg flexion); forearm pointing up and slightly forward; palm facing forward and down; wrist flexed 25 deg; hand: open with fingers spread; fingertips 3.19 m above the floor.
- Left arm: upper arm raised 161 deg from the side of the trunk, pointing up and slightly forward; elbow slightly bent (15 deg flexion); forearm pointing up and slightly forward; palm facing forward and down; wrist flexed 25 deg; hand: open with fingers spread; fingertips 3.19 m above the floor.
- Right leg: hip flexed 14 deg; knee slightly bent (18 deg flexion); thigh pointing down, shin pointing down; ankle plantar-flexed (toes pointed) 45 deg; foot 72 cm above the floor.
- Left leg: hip flexed 14 deg; knee slightly bent (18 deg flexion); thigh pointing down, shin pointing down; ankle plantar-flexed (toes pointed) 45 deg; foot 72 cm above the floor.
- Airborne: lowest point of the body 72 cm above the floor; neither foot touches the ground.
- Technique cue: penetrate the hands over the net, do not just reach up
- Technique cue: pelvis and shoulders parallel to the net
- Technique cue: thumbs up, fingers spread and strong

3. OBJECT_INTERACTION:
- Net: top tape 2.43 m high, 32 cm in front of the hips; fingertips 76 cm above the tape and 26 cm past the net plane into the opponent's court; body stays on its own side.

4. CINEMATIC_CAMERA:
- attacker_view: low-angle shot looking up, from the front (target side), 50mm standard lens, full-body shot. From the attacker's side of the net: a wall of hands above the tape.
- net_profile: eye-level shot, side profile view, 35mm standard lens, full-body shot. Profile along the net shows the arms penetrating over it.
- wide_cinema: eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide from behind the blocker, attacker and ball beyond the net.

5. KINETIC_ENERGY:
- net mesh flexing slightly next to the arms
- hands firm against an incoming spike
- sweat on the forearms catching the arena light
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a volleyball blocker at the top of the jump pressing both hands over the net. Airborne with legs nearly straight and toes pointed down; trunk upright and slightly piked; shoulders square to the net; both arms straight, reaching up and forward over the tape into the opponent's court; hands wide open, fingers spread, palms facing down toward the opponent's floor. Penetrate the hands over the net, do not just reach up. Pelvis and shoulders parallel to the net. Thumbs up, fingers spread and strong. Low-angle shot looking up, from the front (target side), 50mm standard lens, full-body shot. From the attacker's side of the net: a wall of hands above the tape. Net mesh flexing slightly next to the arms; hands firm against an incoming spike. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, hands on the blocker's own side, arms bent at 90 degrees, arms spread so wide the ball passes between them, body passing through the net, feet on the floor
```

## Control images

- `openpose_attacker_view.png` / `.json`: 896x1152, low-angle shot looking up, from the front (target side), 50mm standard lens, full-body shot.
- `openpose_net_profile.png` / `.json`: 896x1152, eye-level shot, side profile view, 35mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_elbow_flex | 15.0 | ..20 | arms nearly straight | S3 (estimate from technique descriptions) |
| r_shoulder_elev | 161.3 | 145.. | shoulders fully flexed, arms reaching up and forward | S3 |
| fwd:r_fingertip:net_top | 25.5 | 15.. | hands penetrate past the net plane (about 36 cm in NCAA women) | S1 |
| up:r_fingertip:net_top | 75.9 | 10.. | hands above the tape (about 17 cm in NCAA women; more in men) | S1 |
| fwd:net_top:r_shoulder | 18.2 | 5.. | body stays on its own side of the net | rules |
| hip_shoulder_sep | 0.0 | -8..8 | pelvis and shoulders parallel to the net | S2 |
| lowest_z | 0.7 | 0.3.. | airborne, block jump | S1 |

## Sources

- [S1] Ficklin et al. 2014, JSSM 13:78: swing vs traditional block (hand penetration 17 cm above and 36.5 cm past the net, NCAA women; search extract) https://www.researchgate.net/publication/260382646
- [S2] ISBS blocking paper: pelvis and shoulders parallel to the net, hand penetration https://ojs.ub.uni-konstanz.de/cpa/article/view/244/203
- [S3] Lobietti, ISBS 2006: block footwork and knee flexion https://ojs.ub.uni-konstanz.de/cpa/article/download/163/123
