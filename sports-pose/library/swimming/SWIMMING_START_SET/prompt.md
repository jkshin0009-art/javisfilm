# SWIMMING_START_SET

Swimmer in the 'take your marks' position of a kick start on the block: left foot at the front edge with toes over it, right foot on the raised back plate, hands gripping the front edge, hips high, head down.

- 이름(ko): 수영 스타트 자세, 스타트대 준비, 킥 스타트, 출발 준비 자세
- names (en): swimming start set, take your marks, kick start on the block, track start

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #SWIMMING_START_SET

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 20 deg; face pointing down and backward. Eyes down at the water in front of the block.
- Torso: trunk line (hips to shoulders) 110 deg forward of vertical, leaning 180 deg to the athlete's left; spine flexed 45 deg over the pelvis; shoulders square with the hips.
- Right arm: upper arm raised 84 deg from the side of the trunk, pointing down and slightly backward; elbow bent (58 deg flexion); forearm pointing down and slightly to the athlete's left; palm facing backward and slightly down; wrist neutral; hand: fingers wrapped firmly around what it holds; fingertips 0.59 m above the water surface.
- Left arm: upper arm raised 84 deg from the side of the trunk, pointing down and slightly backward; elbow bent (58 deg flexion); forearm pointing down and slightly to the athlete's right; palm facing backward and slightly down; wrist neutral; hand: fingers wrapped firmly around what it holds; fingertips 0.59 m above the water surface.
- Right leg (back foot on the kick plate): hip flexed 91 deg; knee bent to about a right angle (102 deg flexion); thigh pointing down and slightly forward, shin pointing backward and slightly down; ankle dorsiflexed 40 deg; ankle 0.95 m above the water surface.
- Left leg (front foot at the edge): hip flexed 113 deg; knee deeply bent (72 deg flexion); thigh pointing forward and down, shin pointing down and slightly backward and slightly to the athlete's right; ankle dorsiflexed 24 deg; foot flat on the floor.
- Base: ankles 44 cm apart (24% of body height, 1.1x shoulder width); every support foot touches the floor, none floats.
- Technique cue: weight slightly back, ready to pull and push
- Technique cue: one foot at the front edge (the rule)
- Technique cue: absolutely still until the start signal

3. OBJECT_INTERACTION:
- Starting block about 0.7 m above the water, top sloping toward the pool.
- Raised back plate (kick plate) at the rear of the block.
- Water surface; the lane rope runs alongside.
- Legal under the World Aquatics rules: the front foot's toes are at the front edge of the block.

4. CINEMATIC_CAMERA:
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view along the pool end, block and water line in frame.
- from_the_water: low-angle shot looking up, from the front (target side), 50mm standard lens, full-body shot. Low from the water in front of the block, the swimmer's cap and shoulders facing camera.
- wide_cinema: high-angle shot looking down, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the blocks, the lanes stretching to the far wall, arena lights.

5. KINETIC_ENERGY:
- perfectly still, tension in the hamstrings
- water flat below the block
- starting light on the block
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a swimmer set on the starting block in the take-your-marks position. Crouched on the starting block: left foot at the front edge with the toes curled over it, right foot back on the raised kick plate with the heel up; both hands gripping the front edge of the block; hips high above the head, back rounded forward; head down, eyes on the water just in front of the block. Weight slightly back, ready to pull and push. One foot at the front edge (the rule). Absolutely still until the start signal. Eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view along the pool end, block and water line in frame. Perfectly still, tension in the hamstrings; water flat below the block. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, swimmer standing on the pool floor, no goggles, body floating high out of the water, wrong number of arms, hair floating without a swim cap, both feet side by side at the back of the block, hands off the block, swimmer already diving, both feet at the back of the starting block, swimmer already diving while the others are still set
```

## Control images

- `openpose_side.png` / `.json`: 1344x768, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_from_the_water.png` / `.json`: 1152x896, low-angle shot looking up, from the front (target side), 50mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, high-angle shot looking down, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: r_leg.ankle = -40 is beyond the usual range -35..60

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| l_knee_flex | 72.3 | 25..95 | front knee bent, shin angled forward | EST |
| r_knee_flex | 101.8 | 65..125 | back knee bent about 90 deg on the kick plate | EST |
| up:head:pelvis | -28.6 | ..0 | hips high, head below the hips looking down | EST |

## Official game rules (World Aquatics Swimming Rules (SW), Facilities Rules (FR) and General Rules (GR))

| rule | what | check on this skeleton |
|---|---|---|
| World Aquatics SW 4.1 | One foot at the front of the block: On 'take your marks' the swimmers immediately take a starting position with at least one foot at the front of the starting platform; the position of the hands does not matter. | OK: inside |
| World Aquatics SW 4.4 | False start: Any swimmer who starts before the starting signal is disqualified; everyone is still in the set position until the signal. | text only |
| equipment | block_height | OK: height_m 0.75 (official 0.5-0.75, World Aquatics FR 2.7 (0.5-0.75 m above the water)) |
| equipment | block_slope | OK: slope_deg 5 (official 0-10, World Aquatics FR 2.7 (slope at most 10 deg)) |
| equipment | pool_depth | OK: depth_m 2.5 (official 2-3.5, World Aquatics FR 2 (at least 2 m)) |

Scene rules for a full match shot (players, uniforms, officials):

- 50 m pool, lanes 2.5 m wide separated by lane ropes, dark lane lines and end-wall targets on the pool floor; backstroke flags across the pool 5 m from each wall. (World Aquatics FR 2)
- Swimwear of textile only: men's suits reach no higher than the navel and no lower than the knee; women's suits leave the neck and shoulders uncovered and reach no lower than the knee. Up to two caps and goggles are allowed. (World Aquatics GR 5)
- Referee and starter at the end of the pool, stroke judges walking the sides, turn judges at each end of every lane. (World Aquatics SW 2)

Rulebook: https://www.worldaquatics.com/rules/competition-regulations

## Sources

- [WA] World Aquatics Swimming Rules SW 4 (start), SW 5 (freestyle), SW 7 (breaststroke), SW 8 (butterfly) and Facilities Rules FR 2 - general knowledge, not re-checked this session https://www.worldaquatics.com/rules/competition-regulations
- [EST] Estimate from standard swimming coaching (no measured joint angle checked this session) 
