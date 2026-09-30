# FISHING_CAST_RELEASE

Right-handed overhead cast at release: rod swept forward and stopped at 10 o'clock, rod arm extended toward the target, weight on the front foot, line shooting out toward the water.

- 이름(ko): 낚시 캐스팅 릴리스, 캐스팅 던지는 순간, 낚싯대 10시 방향, 루어 던지기
- names (en): fishing cast release, forward cast, rod at 10 o'clock, casting a lure

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #FISHING_CAST_RELEASE

2. ANATOMICAL_BONES:
- Gaze & head: head level; face pointing forward and slightly down. Eyes on the target.
- Torso: trunk line (hips to shoulders) 16 deg forward of vertical; spine flexed 8 deg over the pelvis; shoulders square with the hips.
- Right arm (rod hand on the reel seat): upper arm raised 95 deg from the side of the trunk, pointing forward; elbow slightly bent (30 deg flexion); forearm pointing forward and slightly up; palm facing to the athlete's left and slightly down; wrist neutral; hand: fingers wrapped firmly around what it holds; fingertips 1.49 m above the floor.
- Left arm (second hand): upper arm raised 64 deg from the side of the trunk, pointing down and to the athlete's right and slightly forward; elbow bent (46 deg flexion); forearm pointing to the athlete's right and forward; palm facing backward and slightly to the athlete's right; wrist neutral; hand: fingers wrapped firmly around what it holds; fingertips 1.28 m above the floor.
- Right leg: hip extended 12 deg; knee slightly bent (10 deg flexion); thigh pointing down and slightly backward, shin pointing down and slightly backward; ankle neutral; on the ball of the foot, heel raised.
- Left leg (front leg): hip flexed 20 deg; knee slightly bent (20 deg flexion); thigh pointing down, shin pointing down; ankle neutral; foot flat on the floor.
- Base: ankles 49 cm apart (28% of body height, 1.2x shoulder width); every support foot touches the floor, none floats.
- Technique cue: release at 10 o'clock
- Technique cue: follow through toward the target
- Technique cue: keep the rod tip pointed at the target until the lure lands

3. OBJECT_INTERACTION:
- rod (2.3 m): spinning reel hanging under the rod; butt section pointing forward and slightly up, tip 2.33 m above the floor, the upper third bent about 12 deg under load; the line runs from the tip down to the water.
- Water about 0.5 m below the bank; the lure flies toward a spot 18 m out.

4. CINEMATIC_CAMERA:
- side: eye-level shot, side profile view, 35mm standard lens, full-body shot. Side view, the whole rod arc in frame against the sky.
- front_three_quarter: eye-level shot, three-quarter front view, 50mm standard lens, full-body shot. Three-quarter front view from the water side, face and hands sharp.
- wide_cinema: eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the angler over the water, golden hour light.

5. KINETIC_ENERGY:
- line streaking out in a thin arc from the rod tip
- lure small and far over the water
- rod tip vibrating after the stop
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, an angler releasing an overhead cast, line shooting toward the water. Weight shifted onto the left front foot, right heel lifting; right arm extended forward at shoulder height, rod stopped at the 10 o'clock position pointing toward the target; index finger just releasing the line; left hand pulling the butt in toward the belly. Release at 10 o'clock. Follow through toward the target. Keep the rod tip pointed at the target until the lure lands. Eye-level shot, side profile view, 35mm standard lens, full-body shot. Side view, the whole rod arc in frame against the sky. Line streaking out in a thin arc from the rod tip; lure small and far over the water. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, rod pointing down at the water, line not running from the tip, reel on top of a spinning rod, two fishing lines from one rod, several rods tangled on one fish, electric reel with a power cable, motorised reel
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
| fwd:rod_tip:rod_seat | 173.5 | 150.. | rod stopped in front at about 10 o'clock (30 deg above horizontal) | DWR |
| up:rod_tip:rod_seat | 88.2 | 60..160 | rod tip still above the hand at release | DWR |

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
- [EST] Estimate from coaching descriptions (no measured value found this session) 
