Si un nodo falla ocurre lo siguiente:
    * El nodo n falla
    Los nodos que pertenecen a los mismos cliques de replicacion que n, detectan que el mismo lleva tiempo sin enviar heartbeats y lo marcan como down.
    Cada uno de los nodos anteriormente mencionados, analizan si son responsables de la falla del nodo n.
        Esto se realiza viendo en cada uno de los cliques de replicacion en comun con el nodo n, si el nodo actual es el de menor id(El que se encuentra antes en el anillo)
    Hay 5 acciones a llevar a cabo a partir de la baja de n:
        - Un nodo debe hacerse responsable de la falla de n.
        - Este mismo nodo debe almacenar los datos fisicos de n.
        - Replicar los archivos almacenados fisicamente en n(ahora en el nodo responsable) un nodo mas adelante en el anillo(Implica meterlo en el clique de replicacion)
        - Aumentar el numero de replicas para cada uno de los cliques de replicacion que incluian al nodo n.
        - Hacer que todos los nodos que pertenecen a los mismos cliques de replicacion que n, actualicen sus cliques de replicacion para saber del nodo responsable y para excluir al nodo n.
Si un nodo entra en la red ocurre lo siguiente:
    * El nodo n entra en la red
    El nodo anterior al nuevo marca que tiene cambios en la lista next. Se iran actualizando las listas next de los anteriores poco a poco.
    Se actualizan Finger tables y todo eso.
    Replicacion (acciones a llevar a cabo):
        - Pasar los datos fisicos y referencias hacia n desde su sucesor.
        - Literalmente duplicar los cliques de replicacion en n desde su sucesor.
        - Que todos los nodos que pertenecen a los mismos cliques de replicacion que n(anteriormente de su sucesor), actualicen sus cliques de replicacion para saber del nodo n.
        - Excluir el ultimo nodo de cada uno de los cliques de replicacion que involucran al nodo n.

Al insertar un archivo:
    - Agregarlo en la base de datos fisicos y referencias del nodo que le corresponde el tag seleccionado random de la tag-query.
    - Buscar los nodos que le corresponden cada uno de los tags del archivo y agregar la info del archivo en la base de datos de referencias de dichos nodos.
    - Replicar en los nodos del clique de replicacion lidereado por el nodo en el que su base de datos fisicos almacena el nuevo archivo.
Al insertar un tag:
    - Buscar cada uno de los nodos responsables de los tags de la tag-query y hacer la operacion en dichos nodos tanto en la base de datos fisicos como en la de referencias.
    - Agregar una referencia a cada uno de los archivos que cumplen con la tag-query en la base de datos de referencias de los nodos responsables de los tags de la tag-list(tags nuevos).
    - Replicar la operacion partiendo de cada uno de los nodos responsables de los tags de la tag-query, hacia delante en el anillo.
eliminar archivos:
    - Se eliminan los archivos que coinciden con la tag-query de la base de datos fisicos y referencias de cada uno de los nodos responsables de los tags de la tag-query.
    - Se replica la operacion partiendo de cada uno de los nodos responsables de los tags de la tag-query, hacia delante en el anillo.
eliminar tags:
    - Se eliminan los tags de la base de datos fisicos y referencias de cada uno de los nodos responsables de los tags de la tag-query.
    - Se replica la operacion partiendo de cada uno de los nodos responsables de los tags de la tag-query, hacia delante en el anillo.

