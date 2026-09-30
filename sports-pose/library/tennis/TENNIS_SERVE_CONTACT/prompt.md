# TENNIS_SERVE_CONTACT

Right-handed tennis serve at ball contact: airborne, racket arm extended high, ball struck well above the head, left arm tucked in, shoulder over shoulder.

- 이름(ko): 테니스 서브 임팩트, 서브 타점, 테니스 서브 순간, 서브 점프
- names (en): tennis serve contact, serve impact, serve at full reach, tennis serve hit

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #TENNIS_SERVE_CONTACT

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 47 deg, turned 7 deg to the athlete's right of the chest line; face pointing forward and slightly up. Eyes on the contact point.
- Torso: trunk line (hips to shoulders) 22 deg forward of vertical, leaning 24 deg to the athlete's left; spine flexed 10 deg over the pelvis; shoulder line rotated 23 deg to the left of the hip line (hip-shoulder separation).
- Right arm (racket arm): upper arm raised 150 deg from the side of the trunk, pointing forward and up; elbow slightly bent (25 deg flexion); forearm pointing up and slightly forward and slightly to the athlete's left; palm facing forward and slightly down; wrist neutral; hand: fingers wrapped firmly around what it holds; fingertips 2.36 m above the floor.
- Left arm (tucked tossing arm): upper arm raised 45 deg from the side of the trunk, pointing down and slightly to the athlete's right and slightly forward; elbow fully folded (110 deg flexion); forearm pointing up and forward; palm facing to the athlete's right and slightly down; wrist neutral; hand: relaxed, fingers softly curled; fingertips 1.71 m above the floor.
- Right leg: hip extended 10 deg; knee bent (35 deg flexion); thigh pointing down and slightly backward, shin pointing backward and down; ankle plantar-flexed (toes pointed) 45 deg; foot 36 cm above the floor.
- Left leg: hip flexed 15 deg; knee slightly bent (15 deg flexion); thigh pointing down, shin pointing down; ankle plantar-flexed (toes pointed) 45 deg; foot 12 cm above the floor.
- Airborne: lowest point of the body 12 cm above the floor; neither foot touches the ground.
- Technique cue: hit up and out at full reach
- Technique cue: shoulder over shoulder rotation
- Technique cue: tossing arm folds in as the racket arm extends

3. OBJECT_INTERACTION:
- racket (68 cm long): gripped in the right hand, shaft pointing to the athlete's left and up and slightly forward, string face turned forward and slightly down; head centre 2.53 m above the floor; strings and frame clearly visible, one racket only.
- ball (7 cm diameter): center 2.51 m above the floor; touching the racket face.
- Legal under the ITF rules: the ball touches only the racket strings.

4. CINEMATIC_CAMERA:
- net_view: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, telephoto compression, racket strings sharp.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view along the baseline.
- wide_cinema: eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the player, court lines and net ahead, stadium blurred.

5. KINETIC_ENERGY:
- racket head motion blur, ball flattened on the strings
- hair and shirt lifted by the jump
- chalk dust at the baseline
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed tennis player hitting a serve at full reach, airborne. Both feet off the court, legs extended and toes pointed; body rising and tilted so the right shoulder is above the left; right racket arm reaching up almost straight, racket face meeting the ball well above and slightly in front of the head; left arm folded into the chest. Hit up and out at full reach. Shoulder over shoulder rotation. Tossing arm folds in as the racket arm extends. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, telephoto compression, racket strings sharp. Racket head motion blur, ball flattened on the strings; hair and shirt lifted by the jump. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, racket without strings, two rackets, ball merged into the strings, left-handed player, bent racket arm at 90 degrees, ball behind the head, ball touching the player's body, ball resting on the racket strings
```

## Control images

- `openpose_net_view.png` / `.json`: 896x1152, eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot.
- `openpose_side.png` / `.json`: 896x1152, eye-level shot, side profile view, 50mm standard lens, full-body shot.
- `openpose_wide_cinema.png` / `.json`: 1344x768, eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot.

## Checks

- all checks passed (range of motion, floor contact, hand-ball contact, sport rules)

## Sport rules (measured on this skeleton)

| metric | value | allowed | why | source |
|---|---|---|---|---|
| r_elbow_flex | 25.0 | ..45 | elbow about 30 deg at contact, nearly straight | META24 |
| r_shoulder_elev | 150.0 | 95..165 | shoulder elevation about 111 deg (world-class arm abduction 101 deg) | META24, FL03 |
| z:ball | 2.5 | 2.5..2.95 | contact high above the head, about 1.4-1.55 x body height | EST (Li Na 2.5 m = 1.48 x height) |
| lowest_z | 0.1 | 0.05.. | both feet off the ground at contact (jump about 12 cm) | EST |

## Official game rules (ITF Rules of Tennis 2026)

| rule | what | check on this skeleton |
|---|---|---|
| ITF 24 (i) | Ball touching the player: The player loses the point if the ball in play touches the player or anything worn or carried except the racket. | OK: ball is 46 cm from the body |
| ITF 24 (g) | Touching the net: The player loses the point if the player, the racket, or anything worn or carried touches the net, posts, cord, strap or band, or the opponent's court while the ball is in play. | text only |
| ITF 24 (e) | Carry or double hit: Deliberately carrying or catching the ball on the racket, or deliberately touching it more than once, loses the point. | text only |
| equipment | racket_length | OK: length_m 0.685 (official 0.5-0.737, ITF 4 (at most 73.7 cm)) |
| equipment | ball_size | OK: diameter_m 0.067 (official 0.0654-0.0686, ITF Appendix I (6.54-6.86 cm)) |

Scene rules for a full match shot (players, uniforms, officials):

- Court 23.77 x 8.23 m (doubles 10.97 m wide); net 0.914 m at the centre, held by a white strap, 1.07 m at the posts; baseline up to 10 cm wide. (ITF 1)
- Chair umpire on a raised chair beside a net post; line umpires (or electronic line calling) and ball persons crouched at the net posts and the back corners. (ITF 2)
- One racket per player, with a crossed, evenly strung pattern. (ITF 4)

Rulebook: https://www.itftennis.com/media/7221/2026-rules-of-tennis-english.pdf

## Sources

- [META24] Jacquier-Bret & Gorce 2024, meta-analysis of tennis serve kinematics (front knee 64.5 +/- 9.7 deg at trophy; shoulder elevation 110.7 +/- 16.9 deg and elbow 30.1 +/- 15.9 deg at contact) - search extract https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11260724/
- [FL03] Fleisig et al. 2003: world-class servers, arm abduction 101 deg and trunk 48 deg above horizontal at contact, peak external rotation 172 deg https://research-repository.uwa.edu.au/en/publications/kinematics-used-by-word-class-tennis-players-to-produce-high-velo/
- [EST] Estimate from coaching descriptions (no measured value found this session) 
