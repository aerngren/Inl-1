import random
import csv
import matplotlib.pyplot as plt
import numpy as np
from datetime import date


filename ="lagerstatus.csv"

ANTAL_GENOMES = 100
KAPACITET = 800
GENRATIONER = 20000
PARNINGS_CHANS = 0.8
MUTERINGS_CHANS = 0.0001
LASTBILAR = 10
STANNA = 30

class Lager():
    def __init__(self, nytt_lager):
        self.inventering = []
        self.förtjänst = 0
        self.total_vikt = 0
        self.skuld = 0
        self.förtjänst_lastbilar = 0
        self.vikt_lastbilar = 0
        self.fyll_lager(nytt_lager)

    def räkna_lager(self):
        self.förtjänst = 0
        self.total_vikt = 0
        self.skuld = 0
        for item in self.inventering:
            self.total_vikt += float(item['Vikt'])            
            self.förtjänst += int(item['Förtjänst'])
            if int(item['Deadline']) < 0:
                self.skuld -= int(item['Deadline']) ** 2

    def fyll_lager(self, lagerstatus):
        lager = []
        with open(lagerstatus, 'r') as data:
            for line in csv.DictReader(data):
                lager.append(line)
        self.inventering = lager
        self.räkna_lager()

class Lastbil:
    def __init__(self, lager):
        self.last = []
        self.vikt = 0
        self.värde = 0
        self.lager = lager

    def lasta(self, sak):   
        self.last.append(sak)
        self.vikt += float(sak["Vikt"])
        self.värde += float(sak["Förtjänst"])
        self.lager.förtjänst_lastbilar += float(sak["Förtjänst"])
        self.lager.vikt_lastbilar += float(sak["Vikt"])
        self.lager.inventering.remove(sak)
        self.lager.räkna_lager()

    def skapa_plocklista(self, lastbil):
        today = date.today()
        filename = f"Lastbil {lastbil} - {today}.txt"

        with open(filename, "w") as f:
            f.write("Plocklista:\n")
            f.write(f"Total Vikt: {self.vikt:.2f}\n")
            f.write(f"Total Värde: {self.värde:.2f}\n")
            f.write("Saker:\n")
            for last in self.last:
                f.write(f"{last}\n")

lager = Lager(filename)

def random_genome():
    return [1 if random.random() < 0.01 else 0 for _ in range(len(lager.inventering))]

def skapa_genomes():
    return [random_genome() for _ in range(ANTAL_GENOMES)]

def fitness(genomes):
    total_vikt = 0
    total_förtjänst = 0
    for val, sak in zip(genomes, lager.inventering):
        if val == 1:
            total_vikt += float(sak["Vikt"])
            total_förtjänst += int(sak["Förtjänst"])
    if total_vikt > KAPACITET:
        return abs(1/total_vikt)
    return total_förtjänst



def turnering(population, vikt, tournament_size=ANTAL_GENOMES//4):
    deltagare = random.sample(list(zip(population, vikt)), tournament_size)
    bästa_deltagarna = max(deltagare, key=lambda x: x[1])
    return bästa_deltagarna[0]
        
def parning(förelder1, förelder2):
    if len(förelder1) <= 1:
        return förelder1, förelder2

    if random.random() < PARNINGS_CHANS:
        crossover_point = random.randint(1, len(förelder1) - 1)
        return förelder1[:crossover_point] + förelder2[crossover_point:], förelder2[crossover_point:] + förelder1[:crossover_point]
    else:
        return förelder1, förelder2

def mutera(barn):
    for i in range(len(barn)):
        if random.random() < MUTERINGS_CHANS:
            barn[i] = abs(barn[i] -1)
    return barn

def kör_algorithm():
    lastbilarna = []
    for _ in range(LASTBILAR):
        if not lager.inventering:
            print("Lager är tomt! Avslutar algoritmen.")
            break

        population = skapa_genomes()
        generations_med_samma_max = 0  
        föregående_högst_fitness = -1  
        bästa_genomet = None 

        for generation in range(GENRATIONER):
            förtjänst = [fitness(genome) for genome in population]
            ny_population = []
            for _ in range(ANTAL_GENOMES // 2):
                turnering1 = turnering(population, förtjänst)
                turnering2 = turnering(population, förtjänst)
                barn1, barn2 = parning(turnering1, turnering2)
                ny_population.extend([mutera(barn1), mutera(barn2)])
            population = ny_population
            förtjänst = [fitness(genome) for genome in population]
            
            högst_förtjänst = max(förtjänst)
            bästa_index = förtjänst.index(högst_förtjänst)

            bästa_genomet = population[bästa_index]

            total_vikt = sum(float(sak["Vikt"]) for idx, sak in zip(bästa_genomet, lager.inventering) if idx == 1)

            print(f"Generation {generation}: Best Fitness = {högst_förtjänst}: Vikt = {total_vikt}")

            if högst_förtjänst == föregående_högst_fitness:
                generations_med_samma_max += 1
            else:
                generations_med_samma_max = 0 

            föregående_högst_fitness = högst_förtjänst

            if generations_med_samma_max >= STANNA:
                print(f"Samma högsta fitness i {generations_med_samma_max} generationer, packar lastbil.")
                lastbil_ = Lastbil(lager)
                saker = [sak for idx, sak in zip(bästa_genomet, lager.inventering) if idx == 1]
                for sak in saker:
                    lastbil_.lasta(sak)
                lager.räkna_lager()
                lastbilarna.append(lastbil_)
                break

        if lager.total_vikt <= 800 and lager.inventering:
            print("Lager under kapacitet, packar resterande i en lastbil.")
            lastbil_ = Lastbil(lager)
            for sak in lager.inventering:  
                lastbil_.lasta(sak)
            lager.räkna_lager()
            lastbilarna.append(lastbil_)
            break

    return lastbilarna


trucks = kör_algorithm()

for idx, truck in enumerate(trucks):
    print(f"Skapad plocklista för lastbil {idx + 1}:")
    truck.skapa_plocklista(idx+1)


    vikter = [float(sak['Vikt']) for sak in truck.last]
    förtjänst = [float(sak['Förtjänst']) for sak in truck.last]
    ids = [sak['Paket_id'] for sak in truck.last]
    
    plt.figure(figsize=(15, 10))

    plt.subplot(4, 1, 1)
    plt.bar(ids, vikter, color='red', alpha=0.7)
    plt.xlabel('Produkt ID')
    plt.ylabel('Vikt')
    plt.title(f'Lastbil {idx + 1} - Antal paket: {len(truck.last)} - Vikt: {truck.vikt:.2f}')
    plt.xticks(rotation=90)
 
    plt.subplot(4, 1, 2) 
    plt.bar(ids, förtjänst, color='blue', alpha=0.7)
    plt.xlabel('Produkt ID')
    plt.ylabel('Förtjänst')
    plt.title(f'Lastbil {idx + 1} - Förtjänst: {truck.värde:.2f}')
    plt.xticks(rotation=90)

    plt.subplot(4, 2, 5)
    plt.title(f"Lastbil {idx + 1} - Vikt Data")
    x = [f"Medelvärde {np.mean(vikter):.2f}", f"Varians {np.var(vikter):.2f}", f"Standardavvikelse {np.std(vikter):.2f}"]
    y = [np.mean(vikter), np.var(vikter), np.std(vikter)]
    plt.bar(x, y)

    plt.subplot(4, 2, 6)
    plt.title(f"Lastbil {idx + 1} - Förtjänst Data") 
    x = [f"Medelvärde {np.mean(förtjänst):.2f}", f"Varians {np.var(förtjänst):.2f}", f"Standardavvikelse {np.std(förtjänst):.2f}"]
    y = [np.mean(förtjänst), np.var(förtjänst), np.std(förtjänst)]
    plt.bar(x, y)

    plt.tight_layout()  
    plt.show()

lager_vikt = [float(sak["Vikt"]) for sak in lager.inventering]
lager_förtjänst = [float(sak['Förtjänst']) for sak in lager.inventering]

truck_total_vikter = [truck.vikt for truck in trucks]
truck_total_förtjänst = [truck.värde for truck in trucks]

etiketter = [f"Lager Vikt: {lager.total_vikt:.2f}"] + [f"Lastbil {i + 1} Vikt: {truck.vikt:.2f}" for i, truck in enumerate(trucks)]
totala_vikter = [lager.total_vikt] + truck_total_vikter
totala_förtjänster = [lager.förtjänst] + truck_total_förtjänst

plt.figure(figsize=(15, 10))
plt.subplot(4, 1, 1)
plt.bar(etiketter, totala_vikter, color='red', alpha=0.7)
plt.xlabel('Plats')
plt.ylabel('Totalvikt')
plt.title(f'Antal paket kvar i lager: {len(lager.inventering)} - Totalvikt Lager {lager.total_vikt:.2f} - Totalvikt i Lastbilar {lager.vikt_lastbilar:.2f}')
plt.xticks(rotation=45) 

etiketter = [f"Lager Förtjänst: {lager.förtjänst:.2f}"] + [f"Lastbil {i + 1} Förtjänst: {truck.värde:.2f}" for i, truck in enumerate(trucks)]
etiketter += [f"Lager: Straff {lager.skuld}Kr"]
totala_förtjänster += [lager.skuld]

plt.subplot(4, 1, 2) 
plt.bar(etiketter, totala_förtjänster, color='Blue', alpha=0.7)
plt.xlabel('Plats')
plt.ylabel('Förtjänst')
plt.title(f'Totalförtjänst kvar i Lager: {lager.förtjänst:.2f}, förtjänst i lastbilar {lager.förtjänst_lastbilar:.2f}')
plt.xticks(rotation=45) 

plt.subplot(4, 2, 5) 
plt.title(f"Lager - Vikt Data") 
x = [f"Medelvärde {np.mean(lager_vikt):.2f}", f"Varians {np.var(lager_vikt):.2f}", f"Standardavvikelse {np.std(lager_vikt):.2f}"]
y = [np.mean(lager_vikt), np.var(lager_vikt), np.std(lager_vikt)]
plt.bar(x, y)

plt.subplot(4, 2, 6) 
plt.title(f"Lager - Förtjänst Data") 
x = [f"Medelvärde {np.mean(lager_förtjänst):.2f}", f"Varians {np.var(lager_förtjänst):.2f}", f"Standardavvikelse {np.std(lager_förtjänst):.2f}", f"Skuld {lager.skuld}"]
y = [np.mean(lager_förtjänst), np.var(lager_förtjänst), np.std(lager_förtjänst), lager.skuld]
plt.bar(x, y)


plt.tight_layout()  
plt.show()
