# VOLLEYBALL_SPIKE_TAKEOFF

Right-handed volleyball spike, final plant of the approach: both feet planted, knees deeply bent, both arms swung far back, just before the jump.

- 이름(ko): 배구 스파이크 도약, 스파이크 발구름, 스파이크 어프로치 마지막 스텝, 점프 직전 팔 뒤로 젖히기
- names (en): volleyball spike takeoff, spike approach plant, attack approach final step, arm backswing before jump

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #VOLLEYBALL_SPIKE_TAKEOFF

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 59 deg, turned 34 deg to the athlete's left of the chest line; face pointing forward and slightly to the athlete's left and slightly up. Eyes up on the incoming set above the net.
- Torso: trunk line (hips to shoulders) 38 deg forward of vertical; spine flexed 10 deg over the pelvis; shoulders square with the hips.
- Right arm (swung back): upper arm raised 58 deg from the side of the trunk, pointing backward; elbow slightly bent (12 deg flexion); forearm pointing backward; palm facing to the athlete's left; wrist extended (cocked back) 10 deg; hand: open, fingers together and straight; fingertips 1.23 m above the floor.
- Left arm (swung back): upper arm raised 55 deg from the side of the trunk, pointing backward; elbow slightly bent (14 deg flexion); forearm pointing backward; palm facing to the athlete's right and slightly backward; wrist extended (cocked back) 10 deg; hand: open, fingers together and straight; fingertips 1.13 m above the floor.
- Right leg (dominant leg, deeper knee bend): hip flexed 80 deg; knee bent to about a right angle (92 deg flexion); thigh pointing forward and down, shin pointing down and backward; ankle dorsiflexed 33 deg; foot flat on the floor.
- Left leg (closing step, slightly ahead): hip flexed 90 deg; knee bent (64 deg flexion); thigh pointing forward and slightly down, shin pointing down; ankle neutral; foot flat on the floor.
- Base: ankles 44 cm apart (23% of body height, 1.0x shoulder width); every support foot touches the floor, none floats.
- Technique cue: wide, dynamic arm swing loads the jump
- Technique cue: plant heel-to-toe with the feet ahead of the hips so the body leans back into the jump
- Technique cue: knees bent deeply, weight low

3. OBJECT_INTERACTION:
- ball (21 cm diameter): center 3.68 m above the floor; surface 311 cm from the forehead (forward and up and slightly to the athlete's left of it).
- Net: top tape 2.43 m high, 130 cm in front of the hips; the set ball is still rising toward the attack point above and in front.
- Legal under the FIVB rules: no part of the body touches the net or the antennae; neither foot is completely past the centre line; the ball rebounds from a brief contact, it is not caught or held; the player is not the Libero (different jersey colour).

4. CINEMATIC_CAMERA:
- side_low: low-angle shot looking up, side profile view, 35mm standard lens, full-body shot. Sharp focus on the planted feet and the swung-back arms, shallow depth of field.
- front_three_quarter: eye-level shot, three-quarter front view, 50mm standard lens, full-body shot. Knees and arms read clearly, net tape out of frame above.
- wide_cinema: eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide cinematic frame from behind the attacker, court lines leading to the net.

5. KINETIC_ENERGY:
- motion blur on both arms at the end of the backswing
- shoe soles gripping the court, slight squeak dust at the heels
- jersey pulled back by the arm swing
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a volleyball attacker on the last plant step of the spike approach, just before jumping. Both feet planted flat, left foot slightly ahead; right knee bent to about 90 degrees, left knee about 65 degrees; trunk leaning about 38 degrees forward; both arms swung straight back behind the hips, palms facing back, at the end of the backswing; eyes up on the set ball. Wide, dynamic arm swing loads the jump. Plant heel-to-toe with the feet ahead of the hips so the body leans back into the jump. Knees bent deeply, weight low. Low-angle shot looking up, side profile view, 35mm standard lens, full-body shot. Sharp focus on the planted feet and the swung-back arms, shallow depth of field. Motion blur on both arms at the end of the backswing; shoe soles gripping the court, slight squeak dust at the heels. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, arms swung forward, upright torso, feet crossed, one foot in the air, straight knees, player touching the net, hand or arm pressing into the net mesh, body tangled in the net, foot planted on the opponent's side under the net, ball held or cradled in the hands, ball caught against the body
```

## Control images

- `openpose_side_low.png` / `.json`: 1152x896, low-angle shot looking up, side profile view, 35mm standard lens, full-body shot.
- `openpose_front_three_quarter.png` / `.json`: 896x1152, eye-level shot, three-quarter front view, 50mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_knee_flex | 92.0 | 80..100 | dominant knee about 90 deg flexion at the deepest plant (elite males 90, females 84) | S1 |
| l_knee_flex | 64.0 | 55..75 | non-dominant knee about 60-64 deg flexion | S1 |
| trunk_lean_fwd | 38.0 | 30..45 | torso forward incline 33-38 deg | S1 |
| r_arm.elev | 58.0 | 45..60 | arms at maximum backswing, shoulders hyperextended (extension limit about 60 deg) | S2, S3 |
| r_arm.plane | -88.0 | ..-60 | arms swung behind the body, not to the side | S3 |
| r_foot_z | 0.0 | ..0.03 | both feet planted | S1 |
| l_foot_z | 0.0 | ..0.03 | both feet planted | S1 |

## Official game rules (FIVB Official Volleyball Rules 2025-2028 (approved by the 39th FIVB World Congress 2024))

| rule | what | check on this skeleton |
|---|---|---|
| FIVB 11.3.1, 11.4.4 | Touching the net: Contact with the net between the antennae (or with the antenna) during the action of playing the ball, from take-off to landing, is a fault. | OK: closest body part to the net: head, 82 cm |
| FIVB 11.2.2.1, 11.4.3 | Crossing the centre line: Touching the opponent's court with a foot is allowed only if part of the foot stays on or directly above the centre line; a foot completely in the opponent's court is a fault. | OK: all on the near side |
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

- [S1] Fuchs et al. 2019, J Sports Sci 37(21): spike jump plant angles, torso incline, jump height of elite players (search extract) https://www.tandfonline.com/doi/full/10.1080/02640414.2019.1639437
- [S2] Wagner et al. 2009, Int J Sports Med: arm backswing (shoulder hyperextension velocity) predicts jump height https://www.thieme-connect.de/products/ejournals/abstract/10.1055/s-0029-1224177
- [S3] Fuchs et al. 2019, J Sci Med Sport: wide dynamic arm swing in the approach https://www.sciencedirect.com/science/article/abs/pii/S1440244018306170
