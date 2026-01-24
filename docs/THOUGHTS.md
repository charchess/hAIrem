* configuration des personna 
-> specific LLM (api centralisée mais chaque persona peut "preferer" un LLM
  differents, si il est configuré dans le central)

* import de personna
-> vu que les assets sont fournis par le "plugin" (externe)
--> le detourage se fait une fois a l'import et stockage local/interne (eviter de redetourer a chaque fois)
-> envisager l'import de "base" et generation complementaire des images manquantes ?
(l'utilisateur peut fournir une illustration ou juste une description dans
sa "carte" personna)

* definir ce que contient une "carte" (un personna, ses outils, un format
  plus strict)

* pendant l'envoi de texte (bouton envoyer) peut etre ajouter un element
  visuel de refexion (zone de saisie grisée ? bouton en mode sablier ?
renarde qui pense ?) ou gerer une queue ?

* quand la connexion avec le llm n'est pas prete, griser le bouton envoyer ?

* gare a la coherence des tenues entre les images !!!

* ajout d'un element visuel de readiness 

* possibilité de désactiver des persona dans via le dashboard
-> peut etre aussi par commandes ?

* dans le dashboard, la croix de sortie ne marche pas 

* si plusieurs persona parlent en meme temps -> faire des pauses (facon
  light novel) entre les speakers
-> etudier la question (une file trop grosse nuierai a l'interaction,
etudier les alternative possible)
