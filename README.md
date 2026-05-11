# baremage-reservoir
Application industrielle baremage de reservoir

### Quoi de neuf dans cette version ?
1.  **L'Ovalisation :** Si vous choisissez "Enterré", un curseur apparaît. Le code transforme mathématiquement le cercle en ellipse. Un écrasement de 5% réduit le volume en haut et en bas mais élargit le réservoir sur les côtés.
2.  **Volume Mort :** Vous pouvez définir la hauteur de la crépine (en mm). L'application calcule automatiquement combien de litres sont "perdus" au fond.
3.  **Aérien vs Enterré :** L'interface s'adapte pour ne pas encombrer l'utilisateur avec des paramètres inutiles en aérien.
4.  **Mathématiques Robustes :** Utilisation de l'intégrale de sections elliptiques décentrées pour gérer à la fois la pente ET la déformation.

Pour le mettre en ligne, n'oubliez pas d'ajouter `scipy` dans votre fichier `requirements.txt`. C'est l'outil le plus complet disponible pour ce type de besoin !
