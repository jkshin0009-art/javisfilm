# FISHING_CAST_BACK

Right-handed overhead cast at the back stop: spinning rod stopped at the 1 o'clock position behind the shoulder, rod hand beside the ear, left hand on the butt, weight on the back foot.

- 이름(ko): 낚시 캐스팅 백스윙, 오버헤드 캐스팅 준비, 낚싯대 뒤로 젖히기, 캐스팅 1시 방향
- names (en): fishing cast back stop, overhead cast back cast, rod loaded at 1 o'clock, casting wind-up

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #FISHING_CAST_BACK

2. ANATOMICAL_BONES:
- Gaze & head: head level, turned 7 deg to the athlete's left of the chest line; face pointing forward. Eyes on the target spot on the water.
- Torso: trunk line (hips to shoulders) 1 deg backward of vertical; shoulder line rotated 12 deg to the right of the hip line (hip-shoulder separation).
- Right arm (rod hand on the reel seat): upper arm raised 100 deg from the side of the trunk, pointing forward; elbow fully folded (120 deg flexion); forearm pointing up and backward; palm facing to the athlete's left and up; wrist extended (cocked back) 20 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.79 m above the floor.
- Left arm (second hand): upper arm raised 49 deg from the side of the trunk, pointing down and forward and slightly to the athlete's right; elbow bent to about a right angle (89 deg flexion); forearm pointing to the athlete's right and up; palm facing backward and slightly to the athlete's right; wrist extended (cocked back) 5 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.51 m above the floor.
- Right leg: hip flexed 5 deg; knee slightly bent (12 deg flexion); thigh pointing down, shin pointing down; ankle neutral; foot flat on the floor.
- Left leg (front leg): hip flexed 15 deg; knee slightly bent (12 deg flexion); thigh pointing down, shin pointing down; ankle neutral; foot flat on the floor.
- Base: ankles 42 cm apart (23% of body height, 1.0x shoulder width); every support foot touches the floor, none floats.
- Technique cue: stop firmly at 1 o'clock, no drift
- Technique cue: reel the lure up to 8-15 cm from the tip before casting
- Technique cue: the elbow drives the cast, not the shoulder

3. OBJECT_INTERACTION:
- rod (2.3 m): spinning reel hanging under the rod; butt section pointing up and slightly backward and slightly to the athlete's right, tip 3.29 m above the floor, the upper third bent about 25 deg under load.
- Water about 0.5 m below the bank; the casting target 18 m out.

4. CINEMATIC_CAMERA:
- side: eye-level shot, side profile view, 35mm standard lens, full-body shot. Side view, the whole rod arc in frame against the sky.
- front_three_quarter: eye-level shot, three-quarter front view, 50mm standard lens, full-body shot. Three-quarter front view from the water side, face and hands sharp.
- wide_cinema: eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the angler over the water, golden hour light.

5. KINETIC_ENERGY:
- rod tip flexing backward
- lure swinging behind the tip
- wind on the water behind
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, an angler at the back stop of an overhead cast with a spinning rod. Standing with the left foot forward, knees soft; right hand gripping the reel seat beside the right ear at head height, elbow bent about 100 degrees; rod stopped behind the shoulder at the 1 o'clock position, its tip flexing back under the lure's weight; left hand holding the end of the butt in front of the chest; spinning reel hanging under the rod. Stop firmly at 1 o'clock, no drift. Reel the lure up to 8-15 cm from the tip before casting. The elbow drives the cast, not the shoulder. Eye-level shot, side profile view, 35mm standard lens, full-body shot. Side view, the whole rod arc in frame against the sky. Rod tip flexing backward; lure swinging behind the tip. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, rod passing through the head, reel on top of a spinning rod, line not connected to the rod tip, fingers merged into the reel, two fishing lines from one rod, several rods tangled on one fish, electric reel with a power cable, motorised reel
```

## Control images

- `openpose_side.png` / `.json`: 1152x896, eye-level shot, side profile view, 35mm standard lens, full-body shot.
- `openpose_front_three_quarter.png` / `.json`: 896x1152, eye-level shot, three-quarter front view, 50mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| fwd:rod_tip:rod_seat | -114.7 | ..-40 | rod stopped past vertical at about 1 o'clock (30 deg behind vertical) | DWR |
| r_elbow_flex | 120.0 | 80..125 | the elbow drives the cast; hand beside the ear | SCS25, EST |

## Official game rules (IGFA International Angling Rules (records and most sport-fishing tournaments))

| rule | what | check on this skeleton |
|---|---|---|
| IGFA Acts that disqualify a catch | One line on the fish: A fish hooked by more than one line does not count; one angler, one rod, one line. | text only |
| IGFA Equipment Regulations, Reels | Power-driven reel: Power-driven reels of any kind (electric, hydraulic or motor-driven) are prohibited; the angler cranks the reel by hand. | text only |
| equipment | rod_tip_length | OK: tip_len_m 1.95 (official 1.016-6, IGFA Equipment Regulations, Rods (tip at least 101.6 cm)) |
| equipment | rod_butt_length | OK: butt_len_m 0.35 (official 0-0.686, IGFA Equipment Regulations, Rods (butt at most 68.6 cm)) |

Scene rules for a full match shot (players, uniforms, officials):

- One angler per rod: from the strike until the fish is landed or released, only the angler touches the rod, reel and line. (IGFA Angling Regulations)
- Fishing from a boat: helpers may take hold of the leader near the boat and gaff or net the fish, but never touch the rod, reel or main line. (IGFA Angling Regulations)
- Hand-cranked reel only; no electric, hydraulic or motor-driven reel. (IGFA Equipment Regulations, Reels)
- A rod belt (gimbal) or harness may take the butt; the rod does not rest on the gunwale, a rod holder or anything else while the fish is played. (IGFA Equipment Regulations, Harnesses and rod belts)

Rulebook: https://igfa.org/international-angling-rules/

## Sources

- [DWR] Utah DWR / Missouri Dept. of Conservation casting guides: stop the back cast at 1 o'clock, release at 10 o'clock, follow through at the target (search extract) https://mdc.mo.gov/fishing/get-started-fishing/casting
- [SCS25] Biomechanics of spinning casting 2025: the elbow has the largest range and angular velocity, the shoulder plays a small role (abstract extract) https://sciencesport.ru/en/journals/tom-13-no1-2025/articles/biomechanics-spinning-casting-sport-fishing-considering-various
- [EST] Estimate from coaching descriptions (no measured value found this session) 
