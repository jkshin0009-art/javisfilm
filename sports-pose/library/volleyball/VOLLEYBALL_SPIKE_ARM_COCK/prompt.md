# VOLLEYBALL_SPIKE_ARM_COCK

Right-handed volleyball spike in the air, bow-and-arrow arm cock: hitting elbow high and back, non-hitting arm pointing at the ball, back arched.

- 이름(ko): 배구 스파이크 백스윙, 스파이크 활시위 자세, 공중 팔 당기기, 스파이크 준비 동작
- names (en): volleyball spike arm cock, bow and arrow, spike backswing in the air, attack arm cocking

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #VOLLEYBALL_SPIKE_ARM_COCK

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 6 deg, turned 12 deg to the athlete's left of the chest line; face pointing forward and slightly up. Eyes on the ball above and in front.
- Torso: trunk line (hips to shoulders) 23 deg backward of vertical, leaning 7 deg to the athlete's right; spine arched back (extended) 18 deg over the pelvis; shoulder line rotated 21 deg to the right of the hip line (hip-shoulder separation).
- Right arm (hitting arm, cocked): upper arm raised 105 deg from the side of the trunk, pointing to the athlete's right and slightly backward; elbow bent to about a right angle (95 deg flexion); forearm pointing up; palm facing forward and up and slightly to the athlete's right; wrist extended (cocked back) 25 deg; hand: open with fingers spread; upper arm externally rotated 115 deg (forearm laid back); fingertips 2.36 m above the floor.
- Left arm (non-hitting arm, pointing at the ball): upper arm raised 132 deg from the side of the trunk, pointing up and slightly forward; elbow slightly bent (12 deg flexion); forearm pointing up and slightly forward; palm facing to the athlete's right and slightly forward; wrist neutral; hand: relaxed, fingers softly curled; fingertips 2.84 m above the floor.
- Right leg: hip flexed 5 deg; knee bent to about a right angle (85 deg flexion); thigh pointing down, shin pointing backward and slightly down; ankle plantar-flexed (toes pointed) 35 deg; foot 70 cm above the floor.
- Left leg: hip flexed 15 deg; knee deeply bent (70 deg flexion); thigh pointing down and slightly forward, shin pointing backward and down; ankle plantar-flexed (toes pointed) 35 deg; foot 50 cm above the floor.
- Airborne: lowest point of the body 50 cm above the floor; neither foot touches the ground.
- Technique cue: non-hitting arm leads and points at the ball
- Technique cue: hitting shoulder rotated back for trunk rotation
- Technique cue: hitting elbow high, hand at ear height

3. OBJECT_INTERACTION:
- ball (21 cm diameter): center 2.80 m above the floor; surface 20 cm from the left fingertip (to the athlete's left and forward of it); surface 73 cm from the forehead (forward and up and slightly to the athlete's left of it).
- Net: top tape 2.43 m high, 80 cm in front of the hips; the ball is still above and in front of the attacker.
- Legal under the FIVB rules: no part of the body touches the net or the antennae; neither foot is completely past the centre line; the ball rebounds from a brief contact, it is not caught or held; the player is not the Libero (different jersey colour).

4. CINEMATIC_CAMERA:
- side_low: low-angle shot looking up, side profile view, 35mm standard lens, full-body shot. Sharp focus on the cocked hitting arm and the arched back.
- front_three_quarter: low-angle shot looking up, three-quarter front view, 50mm standard lens, full-body shot. Both arms separated clearly: one pointing up at the ball, one drawn back like a bowstring.
- wide_cinema: low-angle shot looking up, from behind, 24mm wide-angle lens, full-body shot. Wide frame from behind the attacker looking at the net and the blockers.

5. KINETIC_ENERGY:
- body at the top of the jump, hair and jersey floating
- slight motion blur on the hitting hand as it cocks back
- chalk-white arena light rim-lighting the arched back
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a volleyball attacker in the air drawing the hitting arm back in a bow-and-arrow position before the spike. Airborne, feet 0.50 m above the floor, knees bent with the shins trailing behind; back arched and hitting shoulder rotated back; right elbow high at shoulder height and bent about 90 degrees, hand beside the ear; left arm straight, pointing up at the ball; chest open toward the ball. Non-hitting arm leads and points at the ball. Hitting shoulder rotated back for trunk rotation. Hitting elbow high, hand at ear height. Low-angle shot looking up, side profile view, 35mm standard lens, full-body shot. Sharp focus on the cocked hitting arm and the arched back. Body at the top of the jump, hair and jersey floating; slight motion blur on the hitting hand as it cocks back. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, hitting elbow below the shoulder, non-hitting arm hanging down, feet touching the floor, arm bent backwards at the elbow, player touching the net, hand or arm pressing into the net mesh, body tangled in the net, foot planted on the opponent's side under the net, ball held or cradled in the hands, ball caught against the body
```

## Control images

- `openpose_side_low.png` / `.json`: 896x1152, low-angle shot looking up, side profile view, 35mm standard lens, full-body shot.
- `openpose_front_three_quarter.png` / `.json`: 896x1152, low-angle shot looking up, three-quarter front view, 50mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, low-angle shot looking up, from behind, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_arm.rot | 115.0 | 100..180 | hitting shoulder externally rotated on the way to maximum external rotation (160-180 deg in spikes) | S1 |
| r_shoulder_elev | 105.0 | 85..125 | hitting upper arm abducted about 90-120 deg, elbow at or above shoulder height | S2 (estimate from technique descriptions) |
| r_elbow_flex | 95.0 | 75..115 | hitting elbow bent about 90 deg, hand near the ear | S2 |
| l_shoulder_elev | 132.0 | 120.. | non-hitting arm raised toward the ball | S3 |
| trunk.flex | -18.0 | ..-8 | upper back arched before the swing | S2 |
| hip_shoulder_sep | -21.3 | ..-10 | hitting shoulder rotated back | S3 |
| lowest_z | 0.5 | 0.3.. | airborne | S4 |

## Official game rules (FIVB Official Volleyball Rules 2025-2028 (approved by the 39th FIVB World Congress 2024))

| rule | what | check on this skeleton |
|---|---|---|
| FIVB 11.3.1, 11.4.4 | Touching the net: Contact with the net between the antennae (or with the antenna) during the action of playing the ball, from take-off to landing, is a fault. | OK: closest body part to the net: l thigh, 61 cm |
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

- [S1] Reeser et al. 2010, Sports Health: maximum external rotation 160-172 deg in spikes and jump serves (search extract) https://pubmed.ncbi.nlm.nih.gov/23015961/
- [S2] Technique descriptions of the bow-and-arrow arm swing, summarised in Giatsis et al. 2022, JSSM https://pubmed.ncbi.nlm.nih.gov/36157399/
- [S3] FIVB Coaches Manual Level II: left arm leads, right shoulder rotates back https://www.fivb.com/wp-content/uploads/2024/03/Coaches_Manual_Level_II_EN.pdf
- [S4] Fuchs et al. 2019, J Sports Sci: elite jump heights 0.37-0.64 m https://www.tandfonline.com/doi/full/10.1080/02640414.2019.1639437
