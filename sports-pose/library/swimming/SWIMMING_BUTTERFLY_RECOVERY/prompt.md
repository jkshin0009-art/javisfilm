# SWIMMING_BUTTERFLY_RECOVERY

Butterfly at mid-recovery: both arms swinging forward together low over the water with straight elbows, head back down between the arms, chest pressing, hips at the surface, feet together in the dolphin kick.

- 이름(ko): 접영 리커버리, 접영 팔 돌리기, 버터플라이, 접영 스트로크
- names (en): butterfly recovery, butterfly stroke arms over the water, fly stroke, butterfly swim

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #SWIMMING_BUTTERFLY_RECOVERY

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 15 deg; face pointing down. Eyes down and slightly forward, just above the water.
- Torso: trunk line (hips to shoulders) 83 deg forward of vertical; spine arched back (extended) 12 deg over the pelvis; shoulders square with the hips.
- Right arm (right arm recovering): upper arm raised 92 deg from the side of the trunk, pointing to the athlete's right; elbow slightly bent (8 deg flexion); forearm pointing to the athlete's right; palm facing up; wrist neutral; hand: open, fingers together and straight; fingertips 0.10 m above the water surface.
- Left arm (left arm recovering): upper arm raised 92 deg from the side of the trunk, pointing to the athlete's left; elbow slightly bent (8 deg flexion); forearm pointing to the athlete's left; palm facing up; wrist neutral; hand: open, fingers together and straight; fingertips 0.10 m above the water surface.
- Right leg: hip flexed 10 deg; knee bent (30 deg flexion); thigh pointing backward, shin pointing backward and slightly up; ankle plantar-flexed (toes pointed) 55 deg; ankle 0.07 m above the water surface.
- Left leg: hip flexed 10 deg; knee bent (30 deg flexion); thigh pointing backward, shin pointing backward and slightly up; ankle plantar-flexed (toes pointed) 55 deg; ankle 0.07 m above the water surface.
- In the water: water line at the level of the back upper; above the surface: back upper, sacrum, right fingertip, left fingertip, right heel, left heel; no contact with the pool floor.
- Technique cue: both arms move together and at the same time
- Technique cue: arms low and relaxed over the water
- Technique cue: head goes down before the hands enter

3. OBJECT_INTERACTION:
- Water surface; the lane rope runs alongside.
- Legal under the World Aquatics rules: both hands are over the water, side by side; feet together, kicking as one.

4. CINEMATIC_CAMERA:
- underwater_side: eye-level shot, side profile view, 28mm wide-angle lens, full-body shot. Underwater side view at the surface line, the body split by the water line, bubbles around the hands.
- front_above: overhead high-angle shot, from the front (target side), 50mm standard lens, full-body shot. From the end of the lane just above the water, the swimmer coming toward camera.
- overhead: overhead high-angle shot, side profile view, 35mm standard lens, full-body shot. High angle from the pool deck, blue lane lines on the pool floor.

5. KINETIC_ENERGY:
- water sheeting off both arms
- spray arcing from the fingertips
- turbulence from the dolphin kick behind
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a swimmer swimming butterfly, both arms swinging forward over the water. Prone at the surface with the shoulders just out of the water; both arms swinging forward together low over the water, straight at the elbows, palms facing back and down; head down between the arms with the face toward the water; hips at the surface; legs together, knees slightly bent in the dolphin kick, toes pointed. Both arms move together and at the same time. Arms low and relaxed over the water. Head goes down before the hands enter. Eye-level shot, side profile view, 28mm wide-angle lens, full-body shot. Underwater side view at the surface line, the body split by the water line, bubbles around the hands. Water sheeting off both arms; spray arcing from the fingertips. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, swimmer standing on the pool floor, no goggles, body floating high out of the water, wrong number of arms, hair floating without a swim cap, one arm forward and one arm back, legs apart kicking alternately, breaststroke kick, one arm forward and the other back, arms recovering under the water, flutter kick in butterfly, frog kick in butterfly
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
| z:r_wrist | 0.1 | 0.02.. | hands swing forward over the water | WA |
| r_elbow_flex | 8.0 | ..25 | arms nearly straight on the recovery | EST |

## Official game rules (World Aquatics Swimming Rules (SW), Facilities Rules (FR) and General Rules (GR))

| rule | what | check on this skeleton |
|---|---|---|
| World Aquatics SW 8.2 | Butterfly: arms forward together over the water: Both arms are brought forward together over the water and backward together under the water throughout the race. | OK: lowest of r_wrist/l_wrist +8 cm against the surface; pairs level, largest difference 0 cm |
| World Aquatics SW 8.3 | Butterfly: legs move together: All up and down movements of the legs are simultaneous; the legs need not be level but may not alternate, and a breaststroke kick is not allowed. | OK: pairs level, largest difference 0 cm |
| equipment | pool_depth | OK: depth_m 2.5 (official 2-3.5, World Aquatics FR 2 (at least 2 m)) |

Scene rules for a full match shot (players, uniforms, officials):

- 50 m pool, lanes 2.5 m wide separated by lane ropes, dark lane lines and end-wall targets on the pool floor; backstroke flags across the pool 5 m from each wall. (World Aquatics FR 2)
- Swimwear of textile only: men's suits reach no higher than the navel and no lower than the knee; women's suits leave the neck and shoulders uncovered and reach no lower than the knee. Up to two caps and goggles are allowed. (World Aquatics GR 5)
- Referee and starter at the end of the pool, stroke judges walking the sides, turn judges at each end of every lane. (World Aquatics SW 2)

Rulebook: https://www.worldaquatics.com/rules/competition-regulations

## Sources

- [WA] World Aquatics Swimming Rules SW 4 (start), SW 5 (freestyle), SW 7 (breaststroke), SW 8 (butterfly) and Facilities Rules FR 2 - general knowledge, not re-checked this session https://www.worldaquatics.com/rules/competition-regulations
- [EST] Estimate from standard swimming coaching (no measured joint angle checked this session) 
