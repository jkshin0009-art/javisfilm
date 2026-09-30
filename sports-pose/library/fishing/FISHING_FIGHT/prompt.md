# FISHING_FIGHT

Angler fighting a fish with a spinning rod: rod butt against the belly, rod raised about 50-60 degrees and bent deeply, right hand on the fore grip, left hand cranking the reel, knees bent and leaning back.

- 이름(ko): 낚시 파이팅, 고기 걸린 순간, 낚싯대 휨, 릴링 파이팅
- names (en): fighting a fish, rod bent pumping, angler reeling in, fish on

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #FISHING_FIGHT

2. ANATOMICAL_BONES:
- Gaze & head: head level; face pointing forward. Eyes on the line where it enters the water.
- Torso: trunk line (hips to shoulders) 16 deg backward of vertical; spine arched back (extended) 8 deg over the pelvis; shoulders square with the hips.
- Right arm (rod hand on the fore grip): upper arm raised 58 deg from the side of the trunk, pointing forward and slightly to the athlete's left and slightly down; elbow bent (57 deg flexion); forearm pointing forward and up and slightly to the athlete's left; palm facing to the athlete's left and down; wrist neutral; hand: fingers wrapped firmly around what it holds; fingertips 1.57 m above the floor.
- Left arm (reel hand on the handle): upper arm raised 36 deg from the side of the trunk, pointing forward and down; elbow bent (63 deg flexion); forearm pointing forward and slightly up and slightly to the athlete's right; palm facing to the athlete's right; wrist extended (cocked back) 8 deg; hand: fingers wrapped firmly around what it holds; fingertips 1.38 m above the floor.
- Right leg: hip flexed 15 deg, abducted 12 deg; knee slightly bent (30 deg flexion); thigh pointing down and slightly forward, shin pointing down; ankle neutral; foot flat on the floor.
- Left leg: hip flexed 17 deg; knee bent (32 deg flexion); thigh pointing down and slightly forward, shin pointing down; ankle neutral; foot flat on the floor.
- Base: ankles 35 cm apart (19% of body height, 0.9x shoulder width); every support foot touches the floor, none floats.
- Technique cue: keep the rod at 45-60 degrees above the water
- Technique cue: lift the rod, then reel while lowering it
- Technique cue: smooth, small pumping strokes, never let the line go slack

3. OBJECT_INTERACTION:
- rod (2.3 m): spinning reel hanging under the rod; butt section pointing up and forward, tip 2.45 m above the floor, the upper third bent about 75 deg under load; the line runs from the tip down to the water.
- The line runs taut from the rod tip down into the water about 10 m out where the fish pulls.
- Legal under the IGFA rules: the angler's own hands hold the rod and turn the reel; the rod butt is tucked against the angler's own belly.

4. CINEMATIC_CAMERA:
- side: eye-level shot, side profile view, 35mm standard lens, full-body shot. Side view, the whole rod arc in frame against the sky.
- front_three_quarter: eye-level shot, three-quarter front view, 50mm standard lens, full-body shot. Three-quarter front view from the water side, face and hands sharp.
- wide_cinema: eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the angler over the water, golden hour light.

5. KINETIC_ENERGY:
- rod bending into a deep arc
- line taut and cutting the water, spray where the fish pulls
- forearm muscles tense
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, an angler fighting a strong fish, pumping the bent rod. Knees bent and body leaning back; rod butt tucked against the belly, rod raised about 55 degrees and bent deeply toward the fish; right hand on the fore grip above the reel, left hand turning the spinning reel handle under the rod; line taut to the water. Keep the rod at 45-60 degrees above the water. Lift the rod, then reel while lowering it. Smooth, small pumping strokes, never let the line go slack. Eye-level shot, side profile view, 35mm standard lens, full-body shot. Side view, the whole rod arc in frame against the sky. Rod bending into a deep arc; line taut and cutting the water, spray where the fish pulls. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, straight rod while fighting, slack line, line not ending in the water, reel on the wrong side, second person holding the rod, helper pulling the line, rod resting on the railing, rod left in a rod holder during the fight, angler pulling the fishing line by hand, line wrapped around the hand, two fishing lines from one rod, several rods tangled on one fish, electric reel with a power cable, motorised reel
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
| r_knee_flex | 29.8 | 20..50 | knees bent, body leaning back against the pull | PAK, EST |
| trunk_lean_fwd | -16.0 | ..0 | leaning back with a straight back | PAK |

## Official game rules (IGFA International Angling Rules (records and most sport-fishing tournaments))

| rule | what | check on this skeleton |
|---|---|---|
| IGFA Angling Regulations; Acts that disqualify a catch | Angler fights the fish alone: The angler must hook, fight and land or boat the fish without the aid of any other person; anyone else touching the rod, reel or line during the fight disqualifies the catch. | OK: r palm 0 cm from rod fore; l palm 0 cm from rod reel |
| IGFA Acts that disqualify a catch | Rod resting on an object: Resting the rod in a rod holder, on the gunwale or on any other object while playing the fish disqualifies the catch; the butt may sit in a rod belt or harness on the angler's body. | OK: rod butt 4 cm from belly |
| IGFA Acts that disqualify a catch | Handlining: Holding or lifting the fish with the line in the hand, or with a rope tied to the line or leader, disqualifies the catch; the fish is brought in with the rod and reel. | text only |
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

- [TMF] takemefishing.org: fight with the rod about 45 deg to the water, pump up toward vertical and reel while lowering; spinning reel hangs under the rod https://www.takemefishing.org/how-to-fish/how-to-catch-fish/how-to-reel-in-fish/
- [PAK] Pakula: lifting past about 60 deg above horizontal gains no line; pressure position 45-60 deg (search extract) https://www.pakula.com.au/index.php/btl/ch-08-training/get-the-rod-out
- [EST] Estimate from coaching descriptions (no measured value found this session) 
