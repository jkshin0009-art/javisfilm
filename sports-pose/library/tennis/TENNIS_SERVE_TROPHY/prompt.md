# TENNIS_SERVE_TROPHY

Right-handed tennis serve at the trophy position: side-on behind the baseline, knees bent, tossing arm straight up, racket arm cocked with the racket up behind the head, left shoulder higher.

- 이름(ko): 테니스 서브 트로피 자세, 서브 준비 자세, 토스 후 무릎 굽힘, 테니스 서브 백스윙
- names (en): tennis serve trophy position, serve toss, serve loading, tennis serve wind-up

## Asset (5 sections)

```
1. SYSTEM_INDEX_CODE: #TENNIS_SERVE_TROPHY

2. ANATOMICAL_BONES:
- Gaze & head: head tilted back 51 deg, turned 34 deg to the athlete's left of the chest line; face pointing up and slightly forward and slightly to the athlete's left. Eyes up on the tossed ball.
- Torso: trunk line (hips to shoulders) 2 deg backward of vertical, leaning 18 deg to the athlete's right; spine arched back (extended) 10 deg over the pelvis; shoulders square with the hips.
- Right arm (racket arm): upper arm raised 80 deg from the side of the trunk, pointing to the athlete's right and slightly down and slightly backward; elbow bent to about a right angle (100 deg flexion); forearm pointing up and slightly forward and slightly to the athlete's right; palm facing forward and slightly to the athlete's right and slightly down; wrist extended (cocked back) 25 deg; hand: fingers wrapped firmly around what it holds; upper arm externally rotated 75 deg (forearm laid back); fingertips 1.62 m above the floor.
- Left arm (tossing arm): upper arm raised 165 deg from the side of the trunk, pointing up and slightly forward; elbow straight (5 deg flexion); forearm pointing up; palm facing forward and slightly to the athlete's right and slightly down; wrist neutral; hand: relaxed, fingers softly curled; fingertips 2.30 m above the floor.
- Right leg: hip flexed 28 deg; knee bent (60 deg flexion); thigh pointing down and slightly forward, shin pointing down and backward; ankle dorsiflexed 13 deg; on the ball of the foot, heel raised.
- Left leg (front leg): hip flexed 32 deg; knee bent (49 deg flexion); thigh pointing down and slightly forward, shin pointing down and slightly backward; ankle dorsiflexed 24 deg; foot flat on the floor.
- Base: ankles 24 cm apart (13% of body height, 0.6x shoulder width); every support foot touches the floor, none floats.
- Technique cue: legs load before the racket drops
- Technique cue: tossing arm stays up while the racket arm cocks
- Technique cue: left shoulder higher than the right

3. OBJECT_INTERACTION:
- racket (68 cm long): gripped in the right hand, shaft pointing up and slightly forward and slightly to the athlete's left, string face turned forward and slightly to the athlete's right and slightly down; head centre 1.88 m above the floor; strings and frame clearly visible, one racket only.
- ball (7 cm diameter): center 3.05 m above the floor; surface 72 cm from the left fingertip (up of it).
- Baseline (white, up to 10 cm wide) just in front of the front foot; the server stands behind it.
- Legal under the ITF rules: both feet stay behind the baseline without touching it.

4. CINEMATIC_CAMERA:
- net_view: eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, telephoto compression, racket strings sharp.
- side: eye-level shot, side profile view, 50mm standard lens, full-body shot. Side view along the baseline.
- wide_cinema: eye-level shot, three-quarter rear view, 24mm wide-angle lens, full-body shot. Wide frame from behind the player, court lines and net ahead, stadium blurred.

5. KINETIC_ENERGY:
- ball at the top of the toss, sharp against the sky
- knees coiled, calves tense
- shirt stretched across the back
```

## Prompt (fill {SUBJECT} and {SETTING}; keep the body mechanics as written)

```
{SUBJECT}, a right-handed tennis player at the trophy position of the serve, ball tossed high. Standing side-on behind the baseline, left foot in front pointing toward the right net post, knees bent about 60 degrees; left tossing arm straight up toward the ball; right racket arm cocked with the elbow at shoulder height and bent about 100 degrees, racket head pointing up behind the head; shoulder line tilted with the left shoulder higher; back slightly arched. Legs load before the racket drops. Tossing arm stays up while the racket arm cocks. Left shoulder higher than the right. Eye-level shot, from the front (target side), 85mm short telephoto lens, full-body shot. From across the net, telephoto compression, racket strings sharp. Ball at the top of the toss, sharp against the sky; knees coiled, calves tense. {SETTING}.
```

## Negative prompt

```
extra fingers, missing fingers, fused fingers, extra limbs, missing limbs, extra arms, extra legs, backward-bending elbow, backward-bending knee, twisted torso, floating feet, feet sinking into the floor, distorted hands, deformed anatomy, duplicated athlete, racket without strings, two rackets, ball merged into the strings, left-handed player, foot on the baseline, tossing arm bent, server's foot on the baseline, ball resting on the racket strings
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
| l_knee_flex | 49.0 | 45..85 | front knee about 64 deg at the trophy position (47-81 across studies) | META24 |
| r_elbow_flex | 100.0 | 70..120 | racket-arm elbow 85-107 deg | META24 |
| r_shoulder_elev | 80.0 | 55..110 | racket-arm shoulder abduction 67-88 deg | META24 |
| l_shoulder_elev | 165.0 | 140.. | tossing arm straight up | KE11 |
| trunk_lean_right | 18.0 | 5.. | shoulder line tilted, left shoulder higher (lateral tilt of the trunk toward the racket side) | KE11 |

## Official game rules (ITF Rules of Tennis 2026)

| rule | what | check on this skeleton |
|---|---|---|
| ITF 16, 18 | Foot fault: During the service motion the server may not touch the baseline or the court inside it with either foot, nor change position by walking or running; jumping is allowed. | OK: all on the near side |
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
- [KE11] Kovacs & Ellenbecker 2011, an 8-stage model for the tennis serve https://pmc.ncbi.nlm.nih.gov/articles/PMC3445225
- [EST] Estimate from coaching descriptions (no measured value found this session) 
