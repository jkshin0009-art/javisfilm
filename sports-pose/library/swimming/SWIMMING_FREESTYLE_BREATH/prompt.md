# SWIMMING_FREESTYLE_BREATH

Front crawl breathing to the right: body rolled about 40 degrees, right arm recovering with a high elbow over the water, left arm extended forward under the surface, face turned sideways with the mouth in the bow-wave trough, flutter kick.

- 이름(ko): 자유형 호흡, 자유형 스트로크, 크롤 영법, 자유형 팔 리커버리
- names (en): freestyle breathing, front crawl breath, crawl stroke, freestyle high elbow recovery

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #SWIMMING_FREESTYLE_BREATH

2. ANATOMICAL_BONES:
- Gaze & head: head level, turned 65 deg to the athlete's right of the chest line; face pointing to the athlete's right and slightly up. One eye above the water looking to the side.
- Torso: trunk line (hips to shoulders) 88 deg forward of vertical; shoulders square with the hips; body rolled 35 deg about its long axis onto the left side.
- Right arm (recovering arm): upper arm raised 100 deg from the side of the trunk, pointing up; elbow fully folded (125 deg flexion); forearm pointing down and to the athlete's right; palm facing backward and up; wrist flexed 10 deg; hand: relaxed, fingers softly curled; fingertips 0.10 m above the water surface.
- Left arm (extended arm at the catch): upper arm raised 170 deg from the side of the trunk, pointing forward; elbow slightly bent (15 deg flexion); forearm pointing forward; palm facing to the athlete's right; wrist flexed 15 deg; hand: open, fingers together and straight; fingertips 0.25 m below the water surface.
- Right leg: hip flexed 0 deg; knee straight (5 deg flexion); thigh pointing backward, shin pointing backward; ankle plantar-flexed (toes pointed) 60 deg; ankle 0.00 m above the water surface.
- Left leg: hip flexed 20 deg; knee bent (35 deg flexion); thigh pointing backward and slightly down, shin pointing backward; ankle plantar-flexed (toes pointed) 55 deg; ankle 0.26 m below the water surface.
- In the water: water line at the level of the sacrum; above the surface: back upper, right fingertip, right heel; no contact with the pool floor.
- Technique cue: keep one goggle in the water when you breathe
- Technique cue: high elbow, relaxed hand on the recovery
- Technique cue: roll the body, not just the head

3. OBJECT_INTERACTION:
- Water surface; the lane rope runs alongside.
- Legal under the World Aquatics rules: the head, back or recovering arm breaks the surface.

4. CINEMATIC_CAMERA:
- underwater_side: eye-level shot, side profile view, 28mm wide-angle lens, full-body shot. Underwater side view at the surface line, the body split by the water line, bubbles around the hands.
- front_above: overhead high-angle shot, from the front (target side), 50mm standard lens, full-body shot. From the end of the lane just above the water, the swimmer coming toward camera.
- overhead: overhead high-angle shot, side profile view, 35mm standard lens, full-body shot. High angle from the pool deck, blue lane lines on the pool floor.

5. KINETIC_ENERGY:
- bow wave curling around the head
- white water and bubbles from the kick
- water droplets streaming off the recovering arm
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a swimmer swimming front crawl, taking a breath to the right. Lying prone at the surface, body rolled about 40 degrees onto the left side; right arm recovering over the water with the elbow high and bent, hand relaxed passing the shoulder near the water; left arm extended forward under the surface, palm down; head turned to the right with one goggle still in the water and the mouth open in the trough of the bow wave; legs long in a narrow flutter kick, toes pointed. Keep one goggle in the water when you breathe. High elbow, relaxed hand on the recovery. Roll the body, not just the head. Eye-level shot, side profile view, 28mm wide-angle lens, full-body shot. Underwater side view at the surface line, the body split by the water line, bubbles around the hands. Bow wave curling around the head; white water and bubbles from the kick. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, swimmer standing on the pool floor, no goggles, body floating high out of the water, wrong number of arms, hair floating without a swim cap, head lifted forward out of the water, straight stiff recovering arm, breathing to the left
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
| z:r_elbow | 0.4 | 0.08.. | high elbow: the recovering elbow clears the water | EST |
| z:l_palm | -0.2 | ..-0.05 | leading hand under the surface at the catch | EST |
| z:nose | -0.0 | -0.08..0.12 | mouth at the surface in the bow-wave trough to breathe | EST |

## Official game rules (World Aquatics Swimming Rules (SW), Facilities Rules (FR) and General Rules (GR))

| rule | what | check on this skeleton |
|---|---|---|
| World Aquatics SW 5.3 | Freestyle: part of the swimmer breaks the surface: Some part of the swimmer must break the surface throughout the race, except during the turn and for up to 15 m after the start and each turn. | OK: highest of crown/back_upper/r_elbow/l_elbow/r_heel/l_heel +41 cm against the surface |
| equipment | pool_depth | OK: depth_m 2.5 (official 2-3.5, World Aquatics FR 2 (at least 2 m)) |

Scene rules for a full match shot (players, uniforms, officials):

- 50 m pool, lanes 2.5 m wide separated by lane ropes, dark lane lines and end-wall targets on the pool floor; backstroke flags across the pool 5 m from each wall. (World Aquatics FR 2)
- Swimwear of textile only: men's suits reach no higher than the navel and no lower than the knee; women's suits leave the neck and shoulders uncovered and reach no lower than the knee. Up to two caps and goggles are allowed. (World Aquatics GR 5)
- Referee and starter at the end of the pool, stroke judges walking the sides, turn judges at each end of every lane. (World Aquatics SW 2)

Rulebook: https://www.worldaquatics.com/rules/competition-regulations

## Sources

- [WA] World Aquatics Swimming Rules SW 4 (start), SW 5 (freestyle), SW 7 (breaststroke), SW 8 (butterfly) and Facilities Rules FR 2 - general knowledge, not re-checked this session https://www.worldaquatics.com/rules/competition-regulations
- [EST] Estimate from standard swimming coaching (no measured joint angle checked this session) 
