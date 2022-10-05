import os
import sys
import random
import numpy
from PIL import Image
from PIL import ImageDraw
import multiprocessing
from copy import deepcopy


POP_PER_GENERATION = 100
MUTATION = 0.02
ADD_GENE = 0.3
REM_GENE = 0.2
INITIAL_GENES = 200

GENETAIONS_PER_IMAGE = 50

try:
    gTarget = Image.open("OdevSoru.png")
except IOError:
    print("Dosya bulunamadı")
    exit()

class Point:

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, o):
        return Point(self.x+o.x, self.y+o.y)

class Color:

    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def shift(self, r, g, b):
        self.r = max(0, min(255, self.r+r))
        self.g = max(0, min(255, self.g+g))
        self.b = max(0, min(255, self.b+b))

    def __str__(self):
        return "({}{}{})".format(self.r, self.g, self.b)


class Gene:

        def __init__(self, size):
            self.size = size
            self.diameter = random.randint(5, 15)
            self.pos = Point(random.randint(0, size[0]), random.randint(0, size[1]))
            self.color = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            self.params = ["diameter", "pos", "color"]

        def mutate(self):
            mutation_size = max(1, int(round(random.gauss(15, 4))))/100
            mutation_type = random.choice(self.params)
            if mutation_type == 'diameter':
                self.diameter = random.randint(5, 15)
            elif mutation_type == 'pos':
                x = random.randint(0, self.size[0])
                y = random.randint(0, self.size[1])
                self.pos = Point(x,y)
            elif mutation_type == "color":
                self.color = Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


class Organism:
    def __init__(self, size, num):
        self.size = size
        self.genes = [Gene(size) for _ in range(num)]

    def mutate(self):
        if len(self.genes) < 200:
            for g in self.genes:
                if MUTATION > random.random():
                    g.mutate()

        else:
            for g in random.sample(self.genes, int(len(self.genes) * MUTATION)):
                g.mutate()

        if ADD_GENE > random.random():
            self.genes.append(Gene(self.size))
        if len(self.genes) > 0 and REM_GENE > random.random():
            self.genes.remove(random.choice(self.genes))

    def drawImage(self):
        image = Image.new('RGB', self.size, (255, 255, 255))
        canvas = ImageDraw.Draw(image)

        for g in self.genes:
            color = (g.color.r, g.color.g, g.color.b)
            canvas.ellipse([g.pos.x-g.diameter, g.pos.y-g.diameter, g.pos.x+g.diameter, g.pos.y+g.diameter], outline = color, fill = color)
        return image


def fitness(im1, im2):
    i1 = numpy.array(im1, numpy.int16)
    i2 = numpy.array(im2, numpy.int16)
    dif = numpy.sum(numpy.abs(i1-i2))
    return (dif/255.0*100)/i1.size

def run(cores):
    if not os.path.exists("Outputs"):
        os.mkdir("Outputs")
    target = gTarget
    generation = 1
    parent = Organism(target.size, INITIAL_GENES)
    prevScore = 101
    score = fitness(parent.drawImage(), target)
    p = multiprocessing.Pool(cores)
    while True:
        print("Generation {}-{}".format(generation, score))
        if generation % GENETAIONS_PER_IMAGE == 0:
            parent.drawImage().save(os.path.join("Outputs", "{}.png".format(generation)))
        generation += 1
        prevScore = score
        children = []
        scores = []
        children.append(parent)

        results = groupMutate(parent, POP_PER_GENERATION-1, p)
        newScores, newChildren = zip(*results)

        children.extend(newChildren)
        scores.extend(newScores)

        winners = sorted(zip(children, scores), key=lambda x:x[1])
        parent, score = winners[0]

def mutateAndTest(o):
    try:
        c = deepcopy(o)
        c.mutate()
        i1 = c.drawImage()
        i2 = gTarget
        return (fitness(i1, i2,),c)
    except KeyboardInterrupt:
        pass

def groupMutate(o, number, p):
    results = p.map(mutateAndTest, [o]*int(number))
    return results

if __name__ == "__main__":
    cores = max(1,multiprocessing.cpu_count()-1)

    if len(sys.argv[1:]) >1:
        args = sys.argv[1:]

        for i, a in enumerate(args):
            if a == "-t":
                cores = int(args[i + 1])

    run(cores)