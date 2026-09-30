# SWIMMING_BREASTSTROKE_BREATH

Breaststroke at the breath: head and shoulders up out of the water, hands together under the chin after the insweep with the elbows under the surface, heels drawn toward the buttocks with the feet flexed and turned out for the kick.

- 이름(ko): 평영 호흡, 평영 스트로크, 평영 킥 준비, 평영
- names (en): breaststroke breath, breaststroke insweep, breaststroke kick recovery, breaststroke

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #SWIMMING_BREASTSTROKE_BREATH

2. ANATOMICAL_BONES:
- Gaze & head: head level; face pointing down and forward. Eyes forward and slightly down along the water surface.
- Torso: trunk line (hips to shoulders) 47 deg forward of vertical; spine arched back (extended) 15 deg over the pelvis; shoulders square with the hips.
- Right arm (right arm finishing the insweep): upper arm raised 45 deg from the side of the trunk, pointing down; elbow fully folded (121 deg flexion); forearm pointing forward and slightly up and slightly to the athlete's left; palm facing to the athlete's left and slightly backward and slightly down; wrist flexed 20 deg; hand: open, fingers together and straight; fingertips 0.07 m above the water surface.
- Left arm (left arm finishing the insweep): upper arm raised 45 deg from the side of the trunk, pointing down; elbow fully folded (121 deg flexion); forearm pointing forward and slightly up and slightly to the athlete's right; palm facing to the athlete's right and slightly backward and slightly down; wrist flexed 20 deg; hand: open, fingers together and straight; fingertips 0.07 m above the water surface.
- Right leg: hip flexed 45 deg, abducted 20 deg; knee fully folded (115 deg flexion); thigh pointing down and slightly to the athlete's right and slightly backward, shin pointing up and backward; ankle dorsiflexed 20 deg; ankle 0.23 m below the water surface.
- Left leg: hip flexed 45 deg, abducted 20 deg; knee fully folded (115 deg flexion); thigh pointing down and slightly to the athlete's left and slightly backward, shin pointing up and backward; ankle dorsiflexed 20 deg; ankle 0.23 m below the water surface.
- In the water: water line at the level of the chest; above the surface: crown, nose, back upper, right fingertip, left fingertip; no contact with the pool floor.
- Technique cue: elbows stay under the water
- Technique cue: hands shoot forward together from the chest
- Technique cue: turn the feet out before the kick

3. OBJECT_INTERACTION:
- Water surface; the lane rope runs alongside.
- Legal under the World Aquatics rules: both elbows are under the surface; left and right mirror each other; the head is up out of the water for the breath.

4. CINEMATIC_CAMERA:
- underwater_side: eye-level shot, side profile view, 28mm wide-angle lens, full-body shot. Underwater side view at the surface line, the body split by the water line, bubbles around the hands.
- front_above: overhead high-angle shot, from the front (target side), 50mm standard lens, full-body shot. From the end of the lane just above the water, the swimmer coming toward camera.
- overhead: overhead high-angle shot, side profile view, 35mm standard lens, full-body shot. High angle from the pool deck, blue lane lines on the pool floor.

5. KINETIC_ENERGY:
- water streaming off the shoulders and cap
- small wave rising in front of the chest
- breath fogging over the water in a cool pool hall
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a swimmer swimming breaststroke, lifting the head to breathe. Head and shoulders up out of the water, chin just above the surface; forearms squeezed together under the chin with the hands meeting in front of the face and both elbows under the water; hips lower in the water; knees bent and heels drawn up toward the buttocks, knees about hip width, feet flexed and turned out ready to kick. Elbows stay under the water. Hands shoot forward together from the chest. Turn the feet out before the kick. Eye-level shot, side profile view, 28mm wide-angle lens, full-body shot. Underwater side view at the surface line, the body split by the water line, bubbles around the hands. Water streaming off the shoulders and cap; small wave rising in front of the chest. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, swimmer standing on the pool floor, no goggles, body floating high out of the water, wrong number of arms, hair floating without a swim cap, elbows lifted above the water, one hand in front of the other, flutter kick, arms reaching back past the hips, breaststroke swimmer lifting the elbows out of the water, scissor kick, one hand ahead of the other
```

## Control images

- `openpose_underwater_side.png` / `.json`: 1344x768, eye-level shot, side profile view, 28mm wide-angle lens, full-body shot.
- `openpose_front_above.png` / `.json`: 1344x768, overhead high-angle shot, from the front (target side), 50mm standard lens, full-body shot.
- `openpose_overhead.png` / `.json`: 1344x768, overhead high-angle shot, side profile view, 35mm standard lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| z:r_elbow | -0.1 | ..-0.02 | elbows stay under the water (SW 7.3) | WA |
| z:nose | 0.2 | 0.05.. | mouth clear of the water to breathe | EST |
| r_knee_flex | 115.0 | 90.. | heels drawn up toward the buttocks for the kick | EST |

## Official game rules (World Aquatics Swimming Rules (SW), Facilities Rules (FR) and General Rules (GR))

| rule | what | check on this skeleton |
|---|---|---|
| World Aquatics SW 7.3 | Breaststroke: elbows under the water: The hands are pushed forward together from the breast on, under or over the water; the elbows stay under the water except for the last stroke before a turn, during the turn and at the finish; the hands are not brought back beyond the hip line except in the first stroke after the start and each turn. | OK: top of the r_elbow -0.14 m (limit 0.0 m); top of the l_elbow -0.14 m (limit 0.0 m) |
| World Aquatics SW 7.3, 7.5 | Breaststroke: arms and legs together, in one horizontal plane: All movements of the arms, and of the legs, are simultaneous and in the same horizontal plane without alternating; the feet are turned out in the propulsive part of the kick; scissor, flutter and downward butterfly kicks are not allowed (except one butterfly kick in the first pull-out). | OK: pairs level, largest difference 0 cm |
| World Aquatics SW 7.4 | Breaststroke: head breaks the surface every cycle: During each complete cycle of one arm stroke and one leg kick, some part of the head breaks the surface. | OK: highest of crown/nose +41 cm against the surface |
| equipment | pool_depth | OK: depth_m 2.5 (official 2-3.5, World Aquatics FR 2 (at least 2 m)) |

Scene rules for a full match shot (players, uniforms, officials):

- 50 m pool, lanes 2.5 m wide separated by lane ropes, dark lane lines and end-wall targets on the pool floor; backstroke flags across the pool 5 m from each wall. (World Aquatics FR 2)
- Swimwear of textile only: men's suits reach no higher than the navel and no lower than the knee; women's suits leave the neck and shoulders uncovered and reach no lower than the knee. Up to two caps and goggles are allowed. (World Aquatics GR 5)
- Referee and starter at the end of the pool, stroke judges walking the sides, turn judges at each end of every lane. (World Aquatics SW 2)

Rulebook: https://www.worldaquatics.com/rules/competition-regulations

## Sources

- [WA] World Aquatics Swimming Rules SW 4 (start), SW 5 (freestyle), SW 7 (breaststroke), SW 8 (butterfly) and Facilities Rules FR 2 - general knowledge, not re-checked this session https://www.worldaquatics.com/rules/competition-regulations
- [EST] Estimate from standard swimming coaching (no measured joint angle checked this session) 
