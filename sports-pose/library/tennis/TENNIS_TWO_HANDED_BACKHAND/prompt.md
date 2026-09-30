# TENNIS_TWO_HANDED_BACKHAND

Right-handed tennis two-handed backhand at contact: right foot stepped forward, both hands on the grip (left above right), ball met in front of the front hip at waist height, arms nearly straight.

- 이름(ko): 테니스 양손 백핸드, 투핸드 백핸드, 백핸드 임팩트, 테니스 백핸드
- names (en): two-handed backhand, tennis backhand contact, double-handed backhand, backhand drive

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #TENNIS_TWO_HANDED_BACKHAND

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 10 deg, turned 6 deg to the athlete's left of the chest line; face pointing forward and slightly down. Eyes on the ball at contact.
- Torso: trunk line (hips to shoulders) 20 deg forward of vertical; spine flexed 8 deg over the pelvis; shoulder line rotated 9 deg to the right of the hip line (hip-shoulder separation).
- Right arm (bottom hand): upper arm raised 45 deg from the side of the trunk, pointing down and slightly forward and slightly to the athlete's left; elbow slightly bent (12 deg flexion); forearm pointing down and slightly forward and slightly to the athlete's left; palm facing backward and down and slightly to the athlete's left; wrist extended (cocked back) 10 deg; hand: fingers wrapped firmly around what it holds; fingertips 0.82 m above the floor.
- Left arm (top hand (drives the stroke)): upper arm raised 53 deg from the side of the trunk, pointing down and slightly forward; elbow straight (2 deg flexion); forearm pointing down and slightly forward; palm facing to the athlete's right and slightly backward and slightly down; wrist extended (cocked back) 15 deg; hand: fingers wrapped firmly around what it holds; fingertips 0.81 m above the floor.
- Right leg (front leg): hip flexed 25 deg; knee slightly bent (25 deg flexion); thigh pointing down, shin pointing down; ankle dorsiflexed 12 deg; foot flat on the floor.
- Left leg: hip flexed 5 deg, abducted 12 deg; knee slightly bent (25 deg flexion); thigh pointing down, shin pointing down and slightly backward; ankle neutral; on the ball of the foot, heel raised.
- Base: ankles 44 cm apart (24% of body height, 1.1x shoulder width); every support foot touches the floor, none floats.
- Technique cue: left hand drives the stroke
- Technique cue: hit through the ball in front of the front hip
- Technique cue: finish high over the right shoulder

3. OBJECT_INTERACTION:
- racket (68 cm long): gripped in the right hand, shaft pointing to the athlete's left and forward, string face turned up and forward and slightly to the athlete's right; head centre 0.86 m above the floor; strings and frame clearly visible, one racket only.
- ball (7 cm diameter): center 0.89 m above the floor; touching the racket face; surface 70 cm from the belly (forward and slightly to the athlete's left and slightly down of it).
- Legal under the ITF rules: the ball touches only the racket strings.

4. CINEMATIC_CAMERA:
- net_view: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, telephoto compression, racket strings sharp.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view along the baseline.
- wide_cinema: eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the player, court lines and net ahead, stadium blurred.

5. KINETIC_ENERGY:
- ball compressing on the strings
- racket motion blur
- shirt twisting with the shoulder turn
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed tennis player hitting a two-handed backhand. Right foot stepped forward toward the net, knees bent; both hands on the grip with the left hand directly above the right; arms nearly straight, racket face meeting the ball in front of the right hip at waist height on the left side of the body; shoulders turned, chin near the right shoulder. Left hand drives the stroke. Hit through the ball in front of the front hip. Finish high over the right shoulder. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, telephoto compression, racket strings sharp. Ball compressing on the strings; racket motion blur. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, racket without strings, two rackets, ball merged into the strings, left-handed player, hands apart on the grip, only one hand on the racket, ball touching the player's body, ball resting on the racket strings
```

## Control images

- `openpose_net_view.png` / `.json`: 1152x896, eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_side.png` / `.json`: 1152x896, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_elbow_flex | 12.0 | ..30 | arms nearly straight at contact | EST |
| dist:r_palm:l_palm | 9.8 | ..16 | both hands together on the grip | EST |
| z:ball | 0.9 | 0.7..1.25 | contact at waist height | EST |

## Official game rules (ITF Rules of Tennis 2026)

| rule | what | check on this skeleton |
|---|---|---|
| ITF 24 (i) | Ball touching the player: The player loses the point if the ball in play touches the player or anything worn or carried except the racket. | OK: ball is 32 cm from the body |
| ITF 24 (g) | Touching the net: The player loses the point if the player, the racket, or anything worn or carried touches the net, posts, cord, strap or band, or the opponent's court while the ball is in play. | text only |
| ITF 24 (h), 25 | Reaching over the net: Hitting the ball before it has passed the net loses the point; a follow-through over the net is allowed when the ball was struck on the player's own side. | text only |
| ITF 24 (e) | Carry or double hit: Deliberately carrying or catching the ball on the racket, or deliberately touching it more than once, loses the point. | text only |
| equipment | racket_length | OK: length_m 0.685 (official 0.5-0.737, ITF 4 (at most 73.7 cm)) |
| equipment | ball_size | OK: diameter_m 0.067 (official 0.0654-0.0686, ITF Appendix I (6.54-6.86 cm)) |

Scene rules for a full match shot (players, uniforms, officials):

- Court 23.77 x 8.23 m (doubles 10.97 m wide); net 0.914 m at the centre, held by a white strap, 1.07 m at the posts; baseline up to 10 cm wide. (ITF 1)
- Chair umpire on a raised chair beside a net post; line umpires (or electronic line calling) and ball persons crouched at the net posts and the back corners. (ITF 2)
- One racket per player, with a crossed, evenly strung pattern. (ITF 4)

Rulebook: https://www.itftennis.com/media/7221/2026-rules-of-tennis-english.pdf

## Sources

- [EST] Estimate from coaching descriptions (no measured value found this session) 
