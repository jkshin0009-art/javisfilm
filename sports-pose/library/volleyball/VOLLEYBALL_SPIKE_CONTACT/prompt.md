# VOLLEYBALL_SPIKE_CONTACT

Right-handed volleyball spike at ball contact: airborne, straight hitting arm high in front of the hitting shoulder.

- 이름(ko): 배구 스파이크 타점, 스파이크 임팩트, 공격 타구 순간, 배구 공격
- names (en): volleyball spike contact, attack hit, spike impact, volleyball attack

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #VOLLEYBALL_SPIKE_CONTACT

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 32 deg, turned 49 deg to the athlete's right of the chest line; face pointing to the athlete's right and forward and slightly up. Eyes locked on the ball at the moment of contact.
- Torso: trunk line (hips to shoulders) 8 deg forward of vertical, leaning 14 deg to the athlete's left; spine flexed 8 deg over the pelvis; shoulder line rotated 20 deg to the left of the hip line (hip-shoulder separation).
- Right arm (hitting arm): upper arm raised 163 deg from the side of the trunk, pointing up; elbow slightly bent (16 deg flexion); forearm pointing up and slightly forward; palm facing forward and slightly to the athlete's right and slightly down; wrist neutral; hand: cupped, fingers slightly curled and spread; fingertips 3.03 m above the floor. Heel of the hand and all five fingers on the upper back half of the ball, wrist starting to snap over it.
- Left arm (non-hitting arm, pulled down to the chest): upper arm raised 40 deg from the side of the trunk, pointing down and slightly forward; elbow bent to about a right angle (100 deg flexion); forearm pointing to the athlete's right and slightly forward and slightly up; palm facing down and slightly to the athlete's right; wrist neutral; hand: relaxed, fingers softly curled; fingertips 1.99 m above the floor. Non-hitting arm has swung down and is tucked close to the chest to speed up trunk rotation.
- Right leg (trailing leg): hip flexed 20 deg; knee bent (55 deg flexion); thigh pointing down and slightly forward, shin pointing down and backward; ankle plantar-flexed (toes pointed) 40 deg; foot 55 cm above the floor.
- Left leg (leading leg): hip flexed 32 deg; knee bent (50 deg flexion); thigh pointing down and slightly forward, shin pointing down and slightly backward; ankle plantar-flexed (toes pointed) 35 deg; foot 55 cm above the floor.
- Airborne: lowest point of the body 55 cm above the floor; neither foot touches the ground.
- Technique cue: hitting shoulder, hip and ball form one line
- Technique cue: contact the ball at full reach in front of the hitting shoulder
- Technique cue: non-hitting arm pulls down as the hitting arm swings through

3. OBJECT_INTERACTION:
- ball (21 cm diameter): center 2.81 m above the floor; touching the right palm; surface 56 cm from the right shoulder (up and slightly forward of it); surface 42 cm from the forehead (up and to the athlete's right and slightly forward of it).
- Net: top tape 2.43 m high, 70 cm in front of the hips; ball contact 38 cm above the tape, on the hitter's own side (29 cm short of the net plane).
- Ball slightly flattened against the palm; one ball only.
- Legal under the FIVB rules: no part of the body touches the net or the antennae; neither foot is completely past the centre line; the ball is struck on the attacker's own side of the net; the ball rebounds from a brief contact, it is not caught or held; the player is not the Libero (different jersey colour).

4. CINEMATIC_CAMERA:
- low_three_quarter: low-angle shot looking up, three-quarter front view, 35mm standard lens, full-body shot. Sharp focus on the hitting hand and ball, shallow depth of field, background crowd soft.
- across_net: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. Blocker's point of view from across the net, net tape crossing the lower frame.
- wide_side: low-angle shot looking up, side profile view, 28mm wide-angle lens, full-body shot. Cinematic 21:9-style wide frame, athlete at the right third, arena lights behind.

5. KINETIC_ENERGY:
- motion blur on the hitting forearm and hand along the downward swing path
- ball compressing against the palm, spin blur on the ball panels
- jersey and hair lifted by the upward jump, sweat droplets flying off the arm
- floor far below the feet, shadow on the court under the athlete
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a volleyball attacker at the peak of a jump spike, striking the ball with a straight right arm high in front of the right shoulder. Airborne body with both feet 0.55 m above the floor and toes pointing down, knees bent; trunk tilted left so the hitting shoulder is higher than the other; right arm almost fully straight overhead, palm on the upper back of the ball; left arm pulled down across the chest; eyes on the ball. Hitting shoulder, hip and ball form one line. Contact the ball at full reach in front of the hitting shoulder. Non-hitting arm pulls down as the hitting arm swings through. Low-angle shot looking up, three-quarter front view, 35mm standard lens, full-body shot. Sharp focus on the hitting hand and ball, shallow depth of field, background crowd soft. Motion blur on the hitting forearm and hand along the downward swing path; ball compressing against the palm, spin blur on the ball panels. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, hitting arm bent at 90 degrees, ball behind the head, hand merged into the ball, body touching or passing through the net, both arms raised symmetrically, feet on the floor, player touching the net, hand or arm pressing into the net mesh, body tangled in the net, foot planted on the opponent's side under the net, spiker reaching over the net to hit the ball on the opponent's side, ball held or cradled in the hands, ball caught against the body
```

## Control images

- `openpose_low_three_quarter.png` / `.json`: 896x1152, low-angle shot looking up, three-quarter front view, 35mm standard lens, full-body shot.
- `openpose_across_net.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_wide_side.png` / `.json`: 1344x768, low-angle shot looking up, side profile view, 28mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_elbow_flex | 16.5 | ..30 | straight arm at contact (FIVB: contact with a straight arm; elbow about 14 deg flexion) | S1, S4 |
| r_shoulder_elev | 162.9 | 120..165 | shoulder abduction about 130 deg at contact | S2, S3 |
| fwd:ball:r_shoulder | 27.0 | 5..45 | ball in front of the hitting shoulder | S4 |
| up:ball:r_shoulder | 60.0 | 55.. | contact at near-full reach above the shoulder | S4 |
| trunk_lean_right | -14.1 | ..-5 | trunk tilts away from the hitting arm to raise the hitting shoulder | S4 (ball-shoulder-hip line) |
| lowest_z | 0.6 | 0.3.. | airborne at contact; elite male jump height about 0.62-0.64 m | S5 |

## Official game rules (FIVB Official Volleyball Rules 2025-2028 (approved by the 39th FIVB World Congress 2024))

| rule | what | check on this skeleton |
|---|---|---|
| FIVB 11.3.1, 11.4.4 | Touching the net: Contact with the net between the antennae (or with the antenna) during the action of playing the ball, from take-off to landing, is a fault. | OK: closest body part to the net: l hand, 16 cm |
| FIVB 11.2.2.1, 11.4.3 | Crossing the centre line: Touching the opponent's court with a foot is allowed only if part of the foot stays on or directly above the centre line; a foot completely in the opponent's court is a fault. | OK: all on the near side |
| FIVB 13.3.1, 11.1.2 | Attack hit in the opponent's space: The attack hit must start within the attacker's own playing space; the hand may pass beyond the net only after the initial contact. | OK: all on the near side |
| FIVB 9.2.2, 9.3.3 | Catch or throw: The ball must be hit, not caught or thrown; it rebounds from the contact. | text only |
| FIVB 19.3.1.2-19.3.1.4 | Libero restrictions: A Libero may not serve, block or attempt to block, nor complete an attack hit with the ball entirely above the net; a front-zone overhand finger pass by the Libero may not be attacked above the net. | text only |
| FIVB 13.2.2, 13.2.3 | Back-row attack: A back-row player attacking a ball entirely above the net must take off behind the attack line (3 m) and may land in the front zone. | text only |
| equipment | net_height | OK: height_m 2.43 (official 2.43-2.45, FIVB 2.1.1) |
| equipment | ball_size | OK: diameter_m 0.21 (official 0.2069-0.2133, FIVB 3.1 (65-67 cm around)) |

Scene rules for a full match shot (players, uniforms, officials):

- Six players per team on court, three front row and three back row. (FIVB 7.3.1)
- At most one Libero on court, in a jersey of a clearly contrasting dominant colour; the Libero never serves, blocks or attacks a ball entirely above the net. (FIVB 19.2, 19.1.3)
- Jersey numbers 1-20 centred on the chest (at least 15 cm tall) and back (at least 20 cm tall); the captain has an 8 x 2 cm stripe under the chest number. (FIVB 4.3.3)
- Team members wear the same jersey, shorts and socks (Libero excepted); shoes without heels. (FIVB 4.3)
- Red-and-white striped antennae stand 80 cm above the net at each side line; the net is black 10 cm mesh with a 7 cm white top band. (FIVB 2.4, 2.3)
- Court 18 x 9 m, white 5 cm lines; the centre line runs under the net and attack lines are 3 m from it on both sides. (FIVB 1.3)
- First referee stands on a referee's stand at one end of the net, eyes about 50 cm above the net; the second referee stands on the floor near the opposite post. (FIVB 23.1, 24.1)
- Line judges with flags stand in the free zone 1-3 m from the court corners. (FIVB 29.1)

Rulebook: https://www.fivb.com/volleyball/the-game/official-volleyball-rules/

## Sources

- [S1] EUDL 2022, open-spike kinematics (elbow 166 deg included angle at contact) - search extract https://eudl.eu/pdf/10.4108/eai.29-6-2022.2326123
- [S2] Reeser et al. 2010, Sports Health, upper-limb biomechanics of the volleyball serve and spike https://pubmed.ncbi.nlm.nih.gov/23015961/
- [S3] Oliveira et al. 2020, systematic review of spike kinematics (abduction 130-133 deg) https://journals.sagepub.com/doi/abs/10.1177/1747954119899881
- [S4] FIVB Coaches Manual Level II (attack: hitting shoulder over the ball, straight arm, ball-shoulder-hip line) https://www.fivb.com/wp-content/uploads/2024/03/Coaches_Manual_Level_II_EN.pdf
- [S5] Fuchs et al. 2019, J Sports Sci 37(21), spike jump kinematics of elite players https://www.tandfonline.com/doi/full/10.1080/02640414.2019.1639437
