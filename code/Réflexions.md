# Réflexions

## Notations

- Déplacement d'un jeton : a1-a2

- Déplacement d'une pile de 2 jetons : a1=a2

- Déplacement d'une pile de 3 jetons : a1*a2

## Codage de l'état d'une case

En tout : 1 + 3 + 5 + 6 = 15, soit 4 bits

- case vide : 1 possibilité

- case avec 1 jeton : 3 possibilités

  - blanc
  - noir
  - neutre  

- case avec une pile de 2 jetons : 5 possibilités

  - neutre-neutre
  - neutre-blanc
  - neutre-noir
  - blanc-blanc
  - noir-noir

- case avec une pile de 3 jetons : 6 possibilités

  - neutre-neutre-noir

  - neutre-noir-noir

  - noir-noir-noir

  - neutre-neutre-blanc

  - neutre-blanc-blanc

  - blanc-blanc-blanc

    