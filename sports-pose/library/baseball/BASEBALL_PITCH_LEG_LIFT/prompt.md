# BASEBALL_PITCH_LEG_LIFT

Right-handed baseball pitcher at the balance point: standing on the right leg on the rubber, left knee lifted above hip height, hands together at the chest, body turned away from the plate.

- 이름(ko): 야구 투구 레그킥, 투수 다리 들기, 밸런스 포인트, 와인드업 정점
- names (en): baseball pitch leg lift, balance point, pitcher knee lift, windup peak

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #BASEBALL_PITCH_LEG_LIFT

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 60 deg, turned 38 deg to the athlete's left of the chest line; face pointing to the athlete's left and down. Eyes on the catcher's mitt over the left shoulder.
- Torso: trunk line (hips to shoulders) 15 deg forward of vertical, leaning 9 deg to the athlete's right; spine flexed 10 deg over the pelvis; shoulders square with the hips.
- Right arm (throwing arm): upper arm raised 32 deg from the side of the trunk, pointing down; elbow fully folded (122 deg flexion); forearm pointing to the athlete's left and up and slightly forward; palm facing down and slightly to the athlete's left; wrist flexed 17 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.28 m above the floor.
- Left arm (glove arm): upper arm raised 19 deg from the side of the trunk, pointing down; elbow fully folded (113 deg flexion); forearm pointing to the athlete's right and forward and slightly up; palm facing to the athlete's right and slightly backward and slightly up; wrist extended (cocked back) 20 deg; hand: cupped, fingers slightly curled and spread; fingertips 1.23 m above the floor.
- Right leg (pivot leg on the rubber): hip flexed 19 deg; knee bent (38 deg flexion); thigh pointing down, shin pointing down and slightly to the athlete's right and slightly backward; ankle dorsiflexed 28 deg; foot flat on the floor.
- Left leg (stride leg): hip flexed 112 deg; knee deeply bent (108 deg flexion); thigh pointing forward and slightly up, shin pointing down; ankle plantar-flexed (toes pointed) 30 deg; foot 42 cm above the floor.
- Base: ankles 63 cm apart (34% of body height, 1.5x shoulder width); every support foot touches the floor, none floats.
- Technique cue: balance over the pivot leg at the top of the leg lift
- Technique cue: controlled coil, trunk not leaning back
- Technique cue: hands together at the chest

3. OBJECT_INTERACTION:
- ball (7 cm diameter): center 1.18 m above the floor; touching the right palm.
- Pitcher's plate (rubber) 61 x 15 cm, white, on top of a mound 25 cm above home plate; the front edge of the plate is 18.44 m from the rear point of home plate.
- Legal under the OBR rules: the pivot foot is on the ground against the pitcher's plate; the stride goes straight toward home plate; a dark glove, a bare pitching hand, a clean white ball.

4. CINEMATIC_CAMERA:
- catcher_view: eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast view from behind the plate, long telephoto compression, sharp focus on the pitcher.
- first_base_side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view from the first-base side: stride and arm path read clearly.
- low_cinema: camera 0.4 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot. Low wide cinematic frame from the grass in front of the mound, stadium lights behind.

5. KINETIC_ENERGY:
- stillness before the drive, dust on the rubber
- jersey hanging still, cap brim shading the eyes
- stadium lights rim-lighting the lifted knee
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed baseball pitcher at the balance point of the windup. Standing tall on the right leg on the rubber, right knee slightly bent; left knee lifted above the hip, lower leg hanging, toes relaxed; body turned side-on and slightly past, left shoulder pointing toward home plate; ball hidden in the glove, both hands together at chest height; head level, chin over the glove shoulder. Balance over the pivot leg at the top of the leg lift. Controlled coil, trunk not leaning back. Hands together at the chest. Eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot. Broadcast view from behind the plate, long telephoto compression, sharp focus on the pitcher. Stillness before the drive, dust on the rubber; jersey hanging still, cap brim shading the eyes. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, both feet in the air, stance knee locked straight, lifted knee too low, chest facing the camera, ball floating outside the glove, a third leg, pivot foot off the pitcher's rubber at the start of the delivery, white or grey pitcher's glove, tape or bandage on the pitching hand, bracelet on the pitching wrist
```

## Control images

- `openpose_catcher_view.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 200mm telephoto lens, full-body shot.
- `openpose_first_base_side.png` / `.json`: 1152x896, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_low_cinema.png` / `.json`: 1344x768, camera 0.4 m above the floor, ground-level low angle looking up, three-quarter front view, 24mm wide-angle lens, full-body shot.

## Checks

- warn: head.flex = 60 is beyond the usual range -65..56

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| l_knee_flex | 108.0 | 90..125 | lead knee flexed about 108 deg at maximum height | OBP-P |
| l_leg.flex | 112.0 | 95..125 | lead hip flexed about 112 deg, thigh above horizontal | OBP-P |
| r_knee_flex | 38.0 | 25..50 | stance knee flexed about 38 deg | OBP-P |
| r_foot_z | 0.0 | ..0.03 | balanced on the pivot foot | CG19 |
| z:l_knee | 1.0 | 1.0.. | lead knee about 65 % of height above the rubber | OBP-P |
| dist:r_palm:l_palm | 5.0 | ..12 | hands together (ball in the glove) at chest height | OBP-P |

## Official game rules (MLB Official Baseball Rules (2025 edition; values unchanged for many seasons))

| rule | what | check on this skeleton |
|---|---|---|
| OBR 5.07(a) | Pivot foot on the pitcher's plate: In the windup and set positions the pitcher faces the batter with the pivot foot in contact with the pitcher's plate (set: the other foot in front of it); a pitch delivered without the pivot foot in contact is an illegal pitch. | OK: inside; feet on the floor |
| OBR 6.02(a)(3), (6), (7) | Balk postures: A balk includes delivering to the batter while not facing the batter, making the pitching motion while not touching the pitcher's plate, and throwing to a base without stepping directly toward it. | text only |
| OBR 3.07, 6.02(c) | Pitcher's glove, hand and ball: The glove may not be white or grey or carry other-coloured material; nothing may be attached to the pitching hand or wrist; no foreign substance on the ball. | text only |
| OBR Definitions of Terms (strike zone) | Strike zone: Over home plate, from the hollow beneath the kneecap up to the midpoint between the top of the shoulders and the top of the uniform pants, judged from the batter's stance. | text only |
| equipment | mound_height | OK: drop_m 0.254 (official 0.251-0.257, OBR 2.01 (10 in above home plate)) |
| equipment | mound_slope | OK: slope 0.0833 (official 0.0813-0.0853, OBR 2.01 (1 in per ft)) |
| equipment | mound_flat_front | OK: top_x_m 0.152 (official 0.142-0.162, OBR 2.01 (slope starts 6 in in front of the rubber)) |
| equipment | ball_size | OK: diameter_m 0.074 (official 0.0728-0.0748, OBR 3.01 (9-9.25 in around)) |

Scene rules for a full match shot (players, uniforms, officials):

- Nine fielders per team. (OBR 1.01)
- The catcher crouches directly behind home plate in the catcher's box; the plate umpire (umpire-in-chief) stands behind the catcher; base umpires stand where they see the bases. (OBR 5.02(a), 8.03)
- All fielders except the catcher stand in fair territory; with the pitcher on the rubber, two infielders are on each side of second base with both feet on the infield dirt. (OBR 5.02(c))
- Batters, base runners and base coaches wear batting helmets (ear flap); the catcher wears a helmet and mask. (OBR 3.08)
- The pitcher's glove is not white or grey (piping excepted) and carries no other-coloured material; nothing is attached to the pitching hand, fingers or wrists (no tape, bandage or bracelet). (OBR 3.07(a), 6.02(c)(7))
- Home plate is a white five-sided slab 43 cm wide; the white pitcher's plate (61 x 15 cm) sits on a mound 25 cm above home plate, 18.44 m away. (OBR 2.02, 2.04)

Rulebook: https://mktg.mlbstatic.com/mlb/official-information/2025-official-baseball-rules.pdf

## Sources

- [OBP-P] Driveline OpenBiomechanics, baseball_pitching (100 pitchers, 411 fastballs, 1.85 +/- 0.07 m): means computed from the dataset's point-of-interest and full-signal files (CC BY-NC-SA 4.0; only summary numbers used here) https://github.com/drivelineresearch/openbiomechanics/tree/main/baseball_pitching
- [CG19] A Clinician's Guide to Analysis of the Pitching Motion (2019): balance point, 90/90 arm position, MER about 170 deg https://pmc.ncbi.nlm.nih.gov/articles/PMC6542879/
- [AJSM24] Windup vs stretch, Am J Sports Med 2024 (higher knee lift from the windup) https://pubmed.ncbi.nlm.nih.gov/38687464/
