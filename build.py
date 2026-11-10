import html
import json
import math
from pathlib import Path
from urllib.parse import quote_plus

WHITE = '#FFFFFF'
MOVE = '#FF8A3D'
PROP = '#9DB4E8'
MAT = '#24479A'
GHOST = 0.26
LIMB = 8
HEAD = 10.5
TRACK = []


def at(p, angle, length):
    a = math.radians(angle)
    return (p[0] + length * math.cos(a), p[1] + length * math.sin(a))


def direction(p, q):
    return math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))


def knee(p, q, l1, l2, bend):
    d = min(math.dist(p, q), l1 + l2 - 0.01)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    return at(p, direction(p, q) + bend * math.degrees(math.acos(max(-1.0, min(1.0, c)))), l1)


def track(points, radius):
    for x, y in points:
        TRACK.extend([(x - radius, y - radius), (x + radius, y + radius)])


def poly(points, color=WHITE, width=LIMB, extra=''):
    track(points, width / 2)
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in points)
    return (f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round"{extra}/>')


def head(c, color=WHITE):
    track([c], HEAD)
    return f'<circle cx="{c[0]:.1f}" cy="{c[1]:.1f}" r="{HEAD}" fill="{color}"/>'


def ghost(*items):
    return f'<g opacity="{GHOST}">' + ''.join(items) + '</g>'


def arrowhead(tip, angle, color=MOVE, size=10):
    back = at(tip, angle + 180, size)
    left = at(back, angle + 90, size * 0.6)
    right = at(back, angle - 90, size * 0.6)
    track([tip, left, right], 1)
    return (f'<polygon points="{tip[0]:.1f},{tip[1]:.1f} {left[0]:.1f},{left[1]:.1f} '
            f'{right[0]:.1f},{right[1]:.1f}" fill="{color}"/>')


def arrow(p, q, color=MOVE, both=False):
    a = direction(p, q)
    start = at(p, a, 7) if both else p
    parts = [poly([start, at(q, a + 180, 7)], color, 3.5), arrowhead(q, a, color)]
    if both:
        parts.append(arrowhead(p, a + 180, color))
    return ''.join(parts)


def arc_arrow(center, r, a0, a1, color=MOVE):
    sweep = 1 if a1 > a0 else 0
    trim = math.degrees(7 / r) * (1 if sweep else -1)
    p0, pe, tip = at(center, a0, r), at(center, a1 - trim, r), at(center, a1, r)
    track([at(center, a0 + (a1 - a0) * i / 8, r) for i in range(9)], 2)
    large = 1 if abs(a1 - a0) > 180 else 0
    path = (f'<path d="M{p0[0]:.1f},{p0[1]:.1f} A{r},{r} 0 {large} {sweep} {pe[0]:.1f},{pe[1]:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>')
    return path + arrowhead(tip, a1 + 90 if sweep else a1 - 90, color)


def svg(label, parts, ground=None, mat_y=None, pad=16, min_width=240):
    xs = [p[0] for p in TRACK]
    ys = [p[1] for p in TRACK]
    TRACK.clear()
    x0, x1, y0, y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
    if ground is not None:
        y1 = max(y1, ground + 8)
    if mat_y is not None:
        y1 = max(y1, mat_y + 14)
    if x1 - x0 < min_width:
        grow = (min_width - (x1 - x0)) / 2
        x0, x1 = x0 - grow, x1 + grow
    back = []
    if mat_y is not None:
        back.append(f'<rect x="{x0 + 10:.1f}" y="{mat_y:.1f}" width="{x1 - x0 - 20:.1f}" height="6" rx="3" fill="{MAT}"/>')
    if ground is not None:
        back.append(f'<line x1="{x0:.1f}" y1="{ground}" x2="{x1:.1f}" y2="{ground}" stroke="{PROP}" stroke-width="2.5" opacity="0.7"/>')
    return (f'<svg viewBox="{x0:.1f} {y0:.1f} {x1 - x0:.1f} {y1 - y0:.1f}" role="img" '
            f'aria-label="{html.escape(label)}" xmlns="http://www.w3.org/2000/svg">' + ''.join(back + parts) + '</svg>')


def plank_body(ground, side=False):
    y = ground - 6
    elbow = (226, y)
    shoulder = at(elbow, -95, 30) if side else (226, y - 30)
    angle = 172.4
    hip, knee_, ankle = at(shoulder, angle, 52), at(shoulder, angle, 92), at(shoulder, angle, 130)
    toe = at(ankle, angle - 90, 13)
    centre = at(shoulder, angle - 180, 7 + HEAD)
    parts = [poly([toe, ankle, knee_, hip, shoulder]), poly([shoulder, at(shoulder, angle - 180, 8)])]
    if side:
        raised = at(shoulder, -80, 30)
        parts.append(poly([(244, y), elbow, shoulder]))
        parts.append(poly([shoulder, raised, at(raised, -80, 27)]))
    else:
        parts.append(poly([shoulder, elbow, (253, y)]))
    parts.append(head(centre))
    return parts, dict(hip=hip, ankle=ankle, shoulder=shoulder, head=centre, angle=angle)


def scene_planche():
    g = 150
    body, j = plank_body(g)
    up = j['angle'] + 90
    guide = poly([at(j['ankle'], up, 17), at(j['head'], up, 17)], MOVE, 3, ' stroke-dasharray="1 8"')
    return svg('Planche : appui sur les avant-bras et la pointe des pieds, corps aligné des talons à la tête',
               body + [guide], mat_y=g - 2)


def scene_planche_laterale():
    g = 150
    body, j = plank_body(g, side=True)
    hip = j['hip']
    return svg('Planche latérale : appui sur un avant-bras et le bord des pieds, hanches hautes, bras du dessus vers le plafond',
               body + [arrow((hip[0], g - 7), (hip[0], hip[1] + 9))], mat_y=g - 2)


def scene_dead_bug():
    g = 160
    y = g - 6
    shoulder, hip = (222, y), (170, y)
    centre = (240, g - 2 - HEAD)
    still_arm = [shoulder, (222, y - 30), (222, y - 57)]
    still_ankle = (132, y - 40)
    still_leg = [hip, (170, y - 40), still_ankle, at(still_ankle, -112, 12)]
    elbow2 = at(shoulder, -30, 30)
    knee2 = at(hip, 188, 40)
    ankle2 = at(knee2, 188, 38)
    return svg('Dead bug : sur le dos, un bras et un genou levés, le bras et la jambe opposés descendent vers le sol',
               [poly(still_leg), poly(still_arm),
                poly([hip, knee2, ankle2, at(ankle2, -100, 12)], MOVE),
                poly([hip, shoulder]), head(centre), poly([shoulder, elbow2, at(elbow2, -30, 27)], MOVE),
                arc_arrow(shoulder, 70, -84, -38), arc_arrow(hip, 72, 222, 196)], mat_y=g - 2)


def scene_pont():
    g = 160
    y = g - 6
    shoulder = (226, y)
    centre = (243.5, g - 2 - HEAD)
    ankle, toe = (132, y - 6), (118, y + 1)
    knee_top = at(ankle, -70, 38)
    hip_top = at(knee_top, direction(knee_top, shoulder), 40)
    hip_low = (180, y)
    knee_low = knee(hip_low, ankle, 40, 38, 1)
    return svg('Pont fessier : sur le dos, pieds à plat, le bassin monte jusqu’à aligner genoux, hanches et épaules',
               [ghost(poly([shoulder, hip_low, knee_low, ankle, toe])),
                poly([shoulder, (197, y + 1), (170, y + 2)]),
                poly([shoulder, hip_top, knee_top, ankle, toe]), head(centre),
                arrow((hip_top[0], hip_top[1] - 12), (hip_top[0], hip_top[1] - 34))], mat_y=g - 2)


def scene_bird_dog():
    g = 160
    y = g - 6
    knee_, hip, ankle = (140, y), (140, y - 40), (102, y)
    shoulder = (192, y - 57)
    centre = at(shoulder, 12, 7 + HEAD)
    elbow2 = at(shoulder, -26, 30)
    knee2 = at(hip, 180, 40)
    ankle2 = at(knee2, 180, 38)
    return svg('Bird dog : à quatre pattes, un bras tendu devant et la jambe opposée tendue derrière, à l’horizontale',
               [poly([hip, knee2, ankle2, at(ankle2, 95, 12)], MOVE),
                poly([at(ankle, 200, 12), ankle, knee_, hip, shoulder]),
                poly([shoulder, (192, y - 27), (192, y)]), poly([shoulder, at(shoulder, 12, 8)]), head(centre),
                poly([shoulder, elbow2, at(elbow2, -26, 27)], MOVE)], mat_y=g - 2)


def chair():
    return ''.join([poly([(58, 147), (114, 147)], PROP, 5), poly([(60, 147), (60, 98)], PROP, 5),
                    poly([(63, 147), (63, 186)], PROP, 4), poly([(110, 147), (110, 186)], PROP, 4)])


def bulgarian_pose(hip, front_ankle, rear_ankle, lean):
    front_knee = knee(hip, front_ankle, 40, 38, -1)
    rear_knee = knee(hip, rear_ankle, 40, 38, -1)
    shoulder = at(hip, lean, 52)
    elbow = at(shoulder, 78, 28)
    return [poly([rear_ankle, rear_knee, hip]), poly([(93, 140), rear_ankle]),
            poly([hip, front_knee, front_ankle, (206, 183)]), poly([hip, shoulder]),
            poly([shoulder, at(shoulder, lean, 8)]), head(at(shoulder, lean, 7 + HEAD)),
            poly([shoulder, elbow, at(elbow, -8, 24)])]


def scene_squat_bulgare():
    g = 186
    front_ankle, rear_ankle = (192, g - 6), (107, 141)
    bottom_hip = at(at(front_ankle, -80, 38), 190, 40)
    return svg('Squat bulgare : pied arrière posé sur une chaise, on descend tout droit jusqu’à la cuisse avant à l’horizontale',
               [chair(), ghost(*bulgarian_pose((168, 104), front_ankle, rear_ankle, -86)),
                *bulgarian_pose(bottom_hip, front_ankle, rear_ankle, -84),
                arrow((240, 72), (240, 114))], ground=g)


def scene_souleve():
    g = 176
    ankle, toe = (168, g - 6), (181, g - 3)
    knee_ = at(ankle, -82, 38)
    hip = at(knee_, -110, 40)
    shoulder = at(hip, -12, 52)
    knee2 = at(hip, 168, 40)
    ankle2 = at(knee2, 168, 38)
    elbow = at(shoulder, 92, 30)
    wrist = at(elbow, 90, 27)
    dumbbell = poly([(wrist[0] - 9, wrist[1] + 2), (wrist[0] + 9, wrist[1] + 2)], PROP, 7)
    return svg('Soulevé de terre sur une jambe : le buste bascule vers l’avant pendant que la jambe libre part en arrière',
               [poly([hip, knee2, ankle2, at(ankle2, 80, 12)]), poly([toe, ankle, knee_, hip, shoulder]),
                poly([shoulder, at(shoulder, -12, 8)]), head(at(shoulder, -12, 7 + HEAD)),
                poly([shoulder, elbow, wrist]), dumbbell,
                arc_arrow(hip, 66, -84, -24), arc_arrow(hip, 52, 102, 156)], ground=g)


def calf_pose(toe, foot_angle):
    ankle = at(toe, foot_angle, 20)
    knee_ = at(ankle, -90, 38)
    hip = at(knee_, -90, 40)
    shoulder = at(hip, -90, 52)
    elbow = at(shoulder, 20, 30)
    free_knee = at(hip, 93, 40)
    return [poly([hip, free_knee, at(free_knee, 112, 34)]),
            poly([at(ankle, foot_angle, 5), toe]), poly([ankle, knee_, hip, shoulder]),
            poly([shoulder, elbow, at(elbow, 8, 27)]), poly([shoulder, at(shoulder, -90, 8)]),
            head(at(shoulder, -90, 7 + HEAD))]


def scene_mollets():
    g = 220
    toe = (168, 186)
    step = (f'<rect x="150" y="190" width="62" height="30" fill="{MAT}" stroke="{PROP}" stroke-width="3"/>'
            + poly([(212, 190), (212, 14)], PROP, 4))
    track([(150, 190), (212, 220)], 2)
    return svg('Mollets sur une marche : l’avant du pied sur le bord, le talon descend sous la marche puis monte sur la pointe',
               [step, ghost(*calf_pose(toe, 160)), *calf_pose(toe, 225), arrow((130, 204), (130, 170))], ground=g)


def scene_pogos():
    g = 180
    ankle = (160, g - 30)
    knee_ = at(ankle, -93, 38)
    hip = at(knee_, -89, 40)
    shoulder = at(hip, -88, 52)
    elbow = at(shoulder, 100, 30)
    marks = ''.join(poly([(x, g - 14), (x, g - 4)], MOVE, 3) for x in (152, 164, 176))
    shadow = f'<ellipse cx="166" cy="{g}" rx="20" ry="4" fill="#0F2A66"/>'
    return svg('Pogos : petits sauts rapides sur l’avant du pied, jambes presque tendues',
               [shadow, poly([at(ankle, 62, 13), ankle, knee_, hip, shoulder]), poly([shoulder, elbow, at(elbow, -20, 27)]),
                poly([shoulder, at(shoulder, -88, 8)]), head(at(shoulder, -88, 7 + HEAD)), marks,
                arrow((202, g - 3), (202, g - 34), both=True)], ground=g)


GAINAGE = [
    dict(id='planche', name='Planche sur les coudes', scene=scene_planche, timer=True,
         why='Les abdos profonds tiennent ton bassin : ta posture reste droite jusqu’au bout du marathon.',
         dose={1: ['30 s', ''], 2: ['45 s', ''], 3: ['60 s', '']},
         steps=['Avant-bras au sol, coudes sous les épaules.',
                'Monte sur la pointe des pieds : ton corps forme une ligne droite des talons à la tête.',
                'Serre abdos et fessiers, regarde le sol, respire normalement.'],
         avoid='Les fesses trop hautes, ou le bas du dos qui se creuse.',
         easier='Genoux au sol.', harder='Décolle un pied quelques secondes, puis l’autre.',
         video='planche abdominale sur les coudes bonne position'),
    dict(id='planche-laterale', name='Planche latérale', scene=scene_planche_laterale, timer=True,
         why='Les obliques et le moyen fessier empêchent ton bassin de s’affaisser à chaque appui.',
         dose={1: ['25 s', 'par côté'], 2: ['35 s', 'par côté'], 3: ['40 s', 'par côté']},
         steps=['Allongé sur le côté, coude sous l’épaule, jambes tendues l’une sur l’autre.',
                'Pousse dans le coude et le bord du pied pour décoller les hanches.',
                'Corps bien droit, bras du dessus vers le plafond. Puis l’autre côté.'],
         avoid='Les hanches qui retombent ou qui partent en arrière.',
         easier='Genou du dessous au sol.', harder='Lève la jambe du dessus de quelques centimètres.',
         video='planche latérale sur le coude'),
    dict(id='dead-bug', name='Dead bug', scene=scene_dead_bug,
         why='Ton tronc reste immobile pendant que bras et jambes bougent, comme quand tu cours.',
         dose={1: ['6', 'par côté'], 2: ['8', 'par côté, lentement'], 3: ['10', 'par côté, lentement']},
         steps=['Sur le dos, bras tendus vers le plafond, genoux pliés à 90° au-dessus des hanches.',
                'Plaque le bas du dos contre le sol et garde-le collé.',
                'Descends lentement un bras derrière la tête et la jambe opposée vers le sol, sans les poser.',
                'Reviens au centre, puis l’autre côté.'],
         avoid='Le bas du dos qui décolle. Si ça arrive, descends moins bas.',
         easier='Ne bouge que les jambes.', harder='Descends en 3 secondes.',
         video='dead bug exercice gainage'),
    dict(id='pont-fessier', name='Pont fessier', scene=scene_pont,
         why='Les fessiers sont le moteur de ta poussée à chaque foulée.',
         dose={1: ['12', 'sur 2 jambes'], 2: ['10', 'par jambe, sur 1 jambe'], 3: ['12', 'par jambe, sur 1 jambe, 2 s en haut']},
         steps=['Sur le dos, genoux pliés, pieds à plat près des fesses, bras le long du corps.',
                'Pousse dans les talons et monte le bassin jusqu’à aligner genoux, hanches et épaules.',
                'Serre les fessiers en haut, redescends lentement.',
                'Sur 1 jambe (niveaux 2 et 3) : tends l’autre jambe dans le prolongement de la cuisse, le bassin reste horizontal.'],
         avoid='Cambrer le bas du dos pour monter plus haut.',
         easier='Sur 2 jambes, moins haut.', harder='Pieds posés sur une chaise.',
         video='pont fessier une jambe'),
    dict(id='bird-dog', name='Bird dog', scene=scene_bird_dog,
         why='Il gaine le dos et coordonne bras et jambe opposés, comme ta foulée.',
         dose={1: ['6', 'par côté'], 2: ['8', 'par côté, 2 s tenues'], 3: ['8', 'par côté, 2 s tenues']},
         steps=['À 4 pattes, mains sous les épaules, genoux sous les hanches.',
                'Tends en même temps un bras devant et la jambe opposée derrière, à l’horizontale.',
                'Reviens, puis l’autre côté.'],
         avoid='Le bassin qui pivote ou le dos qui se creuse : imagine un verre d’eau posé sur tes reins.',
         easier='Ne tends que la jambe.', harder='Entre deux répétitions, ramène coude et genou sous le ventre sans les poser.',
         video='bird dog exercice gainage'),
]

JAMBES = [
    dict(id='squat-bulgare', name='Squat bulgare', scene=scene_squat_bulgare,
         why='Quadriceps et fessiers sur une jambe : la force qui amortit chaque réception.',
         dose={1: ['8', 'par jambe, sans charge'], 2: ['10', 'par jambe, descente en 3 s'], 3: ['8', 'par jambe, 2 haltères de 7 kg']},
         steps=['Dos à une chaise, pose le dessus du pied arrière sur l’assise.',
                'Avance le pied avant assez loin pour qu’en bas ton genou reste au-dessus du pied.',
                'Descends tout droit, genou arrière vers le sol, jusqu’à la cuisse avant à l’horizontale.',
                'Remonte en poussant dans le talon avant. Toutes les répétitions d’une jambe, puis l’autre.'],
         avoid='Le genou avant qui rentre vers l’intérieur.',
         easier='Fente arrière, sans chaise.', harder='Descente en 3 secondes avec les haltères.',
         video='squat bulgare poids du corps chaise'),
    dict(id='souleve-de-terre', name='Soulevé de terre sur une jambe', scene=scene_souleve,
         why='Ischios, fessiers et équilibre de la cheville. Il protège les ischios, souvent touchés en marathon.',
         dose={1: ['8', 'par jambe, sans charge'], 2: ['8', 'par jambe, 1 haltère dans la main opposée'], 3: ['10', 'par jambe, 2 haltères']},
         steps=['Debout sur une jambe, genou légèrement fléchi.',
                'Bascule le buste vers l’avant en reculant la hanche : la jambe libre part en arrière dans le prolongement du dos.',
                'Descends jusqu’à sentir l’arrière de la cuisse, buste presque à l’horizontale.',
                'Remonte en serrant le fessier.'],
         avoid='Le dos rond, ou le bassin qui s’ouvre : le pied arrière pointe vers le sol.',
         easier='Une main contre un mur pour l’équilibre.', harder='Un haltère dans chaque main.',
         video='soulevé de terre une jambe haltère'),
    dict(id='mollets', name='Mollets sur une marche', scene=scene_mollets,
         why='Mollets et tendon d’Achille encaissent le plus en marathon. Genou fléchi, tu cibles aussi le muscle profond, le soléaire.',
         dose={1: ['12 + 12', 'par jambe, genou tendu puis fléchi'], 2: ['12 + 12', 'par jambe, genou tendu puis fléchi'],
               3: ['12 + 12', 'par jambe, avec 1 haltère']},
         steps=['Sur une marche, l’avant du pied sur le bord, talon dans le vide, une main au mur.',
                'Sur une jambe, monte sur la pointe en 1 seconde.',
                'Redescends en 3 secondes, talon sous le niveau de la marche.',
                'Fais la série genou tendu, puis la même genou légèrement fléchi.'],
         avoid='Rebondir en bas ou aller vite : c’est la descente lente qui renforce le tendon.',
         easier='Sur 2 pieds.', harder='Un haltère dans la main libre.',
         video='mollets sur marche excentrique genou fléchi'),
    dict(id='pogos', name='Pogos', scene=scene_pogos,
         why='Des chevilles toniques renvoient l’énergie comme un ressort : chaque foulée te coûte moins.',
         dose={1: [None, 'à partir du niveau 2'], 2: ['20', 'sauts'], 3: ['30', 'sauts']},
         steps=['Debout, pieds écartés de la largeur des hanches, genoux presque tendus.',
                'Petits sauts rapides sur place, sur l’avant du pied.',
                'Contacts au sol très courts, les talons ne touchent pas.'],
         avoid='Plier les genoux pour sauter haut : tout vient des chevilles.',
         easier='Montées rapides sur la pointe des pieds, sans décoller.', harder='Quelques sauts de plus.',
         video='pogo jumps course à pied'),
]


PLAY = ('<svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8.6" '
        'fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8.2 6.3 L13.8 10 L8.2 13.7 Z" fill="currentColor"/></svg>')


def lane(index, ex):
    e = html.escape
    dose = json.dumps(ex['dose'], ensure_ascii=False)
    timer = ''
    if ex.get('timer'):
        seconds = {lvl: int(v[0].split()[0]) for lvl, v in ex['dose'].items()}
        timer = (f'<button class="timer" type="button" data-seconds=\'{json.dumps(seconds)}\'>'
                 '<span class="timer-label">Lancer le chrono</span></button>')
    steps = ''.join(f'<li>{e(s)}</li>' for s in ex['steps'])
    video = 'https://www.youtube.com/results?search_query=' + quote_plus(ex['video'])
    return f'''
<article class="lane" id="{ex['id']}">
  <div class="lane-head">
    <span class="lane-no" aria-hidden="true">{index}</span>
    <div>
      <h3>{e(ex['name'])}</h3>
      <p class="why">{e(ex['why'])}</p>
    </div>
  </div>
  <figure class="pose">{ex['scene']()}</figure>
  <div class="dose" data-dose='{e(dose)}'>
    <p><strong class="dose-value"></strong> <span class="dose-detail"></span></p>
    {timer}
  </div>
  <ol class="steps">{steps}</ol>
  <p class="avoid"><strong>À éviter.</strong> {e(ex['avoid'])}</p>
  <p class="variant"><strong>Plus facile :</strong> {e(ex['easier'])}<br><strong>Plus dur :</strong> {e(ex['harder'])}</p>
  <a class="video" href="{e(video)}" target="_blank" rel="noopener">{PLAY}Voir des démos vidéo</a>
</article>'''


TEMPLATE = (Path(__file__).parent / 'template.html').read_text()
page = (TEMPLATE
        .replace('%%GAINAGE%%', ''.join(lane(i, ex) for i, ex in enumerate(GAINAGE, 1)))
        .replace('%%JAMBES%%', ''.join(lane(i, ex) for i, ex in enumerate(JAMBES, 1))))
(Path(__file__).parent / 'index.html').write_text(page)
print('index.html', len(page), 'bytes')
