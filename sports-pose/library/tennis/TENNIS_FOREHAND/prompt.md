# TENNIS_FOREHAND

Right-handed tennis forehand at contact from an open stance: feet parallel to the baseline, knees bent, hips and shoulders turned toward the net, ball met in front at waist height, left arm across the body.

- 이름(ko): 테니스 포핸드, 포핸드 임팩트, 오픈 스탠스 포핸드, 테니스 스트로크
- names (en): tennis forehand, forehand contact, open stance forehand, groundstroke

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #TENNIS_FOREHAND

2. ANATOMICAL_BONES:
- Gaze & head: head tilted down 19 deg, turned 36 deg to the athlete's right of the chest line; face pointing forward and to the athlete's right and slightly down. Eyes on the ball at contact.
- Torso: trunk line (hips to shoulders) 20 deg forward of vertical, leaning 6 deg to the athlete's left; spine flexed 8 deg over the pelvis; shoulder line rotated 16 deg to the left of the hip line (hip-shoulder separation).
- Right arm (racket arm): upper arm raised 40 deg from the side of the trunk, pointing down and slightly to the athlete's right; elbow slightly bent (25 deg flexion); forearm pointing down and slightly forward and slightly to the athlete's right; palm facing forward and slightly down and slightly to the athlete's left; wrist extended (cocked back) 35 deg; hand: fingers wrapped firmly around what it holds; fingertips 0.89 m above the floor.
- Left arm (balance arm across the body): upper arm raised 60 deg from the side of the trunk, pointing down and slightly to the athlete's right and slightly forward; elbow deeply bent (70 deg flexion); forearm pointing forward and slightly up; palm facing to the athlete's right and slightly down; wrist neutral; hand: relaxed, fingers softly curled; fingertips 1.36 m above the floor.
- Right leg: hip flexed 25 deg; knee slightly bent (23 deg flexion); thigh pointing down, shin pointing down; ankle dorsiflexed 8 deg; foot flat on the floor.
- Left leg: hip flexed 30 deg, abducted 22 deg; knee slightly bent (30 deg flexion); thigh pointing down and slightly to the athlete's left and slightly forward, shin pointing down; ankle plantar-flexed (toes pointed) 15 deg; on the ball of the foot, heel raised.
- Base: ankles 53 cm apart (29% of body height, 1.3x shoulder width); every support foot touches the floor, none floats.
- Technique cue: hit out in front of the body
- Technique cue: hips turn before the shoulders
- Technique cue: left arm catches the racket on the follow-through

3. OBJECT_INTERACTION:
- racket (68 cm long): gripped in the right hand, shaft pointing to the athlete's right, string face turned forward and slightly down; head centre 0.93 m above the floor; strings and frame clearly visible, one racket only.
- ball (7 cm diameter): center 0.91 m above the floor; touching the racket face; surface 103 cm from the belly (to the athlete's right and slightly forward of it).
- Legal under the ITF rules: the ball touches only the racket strings.

4. CINEMATIC_CAMERA:
- net_view: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, telephoto compression, racket strings sharp.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view along the baseline.
- wide_cinema: eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the player, court lines and net ahead, stadium blurred.

5. KINETIC_ENERGY:
- ball compressing on the strings, felt fibres blurred
- racket motion blur across the frame
- sneakers sliding on the hard court
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed tennis player hitting a forehand from an open stance. Feet wide and parallel to the baseline, knees bent, weight on the right leg; hips and shoulders turned toward the net; right arm slightly bent, racket face meeting the ball in front of the body at waist height, racket shaft roughly level; left arm folded across the body. Hit out in front of the body. Hips turn before the shoulders. Left arm catches the racket on the follow-through. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, telephoto compression, racket strings sharp. Ball compressing on the strings, felt fibres blurred; racket motion blur across the frame. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, racket without strings, two rackets, ball merged into the strings, left-handed player, ball behind the body at contact, ball touching the player's body, ball resting on the racket strings
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
| r_knee_flex | 23.0 | 20..60 | knees bent, loaded legs (faster forehands use more knee flexion) | SEE, EST |
| z:ball | 0.9 | 0.7..1.25 | contact between waist and chest height | EST |
| fwd:ball:pelvis | 59.0 | 15..70 | ball met in front of the body | EST |
| stance_over_shoulders | 1.3 | 1.1.. | wide open stance, feet parallel to the baseline | EST |

## Official game rules (ITF Rules of Tennis 2026)

| rule | what | check on this skeleton |
|---|---|---|
| ITF 24 (i) | Ball touching the player: The player loses the point if the ball in play touches the player or anything worn or carried except the racket. | OK: ball is 45 cm from the body |
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

- [SEE] Seeley et al.: faster forehands show larger trunk rotation, knee and hip flexion before impact (search extract) https://lida.sport-iat.de/twm/Record/4023740
- [EST] Estimate from coaching descriptions (no measured value found this session) 
