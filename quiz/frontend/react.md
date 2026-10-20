# React

## react-que-es
¿Qué es React y qué problema resuelve?
tags: frecuente, fundamentos

- [x] Una librería para construir interfaces con componentes y UI declarativa según el estado
- [ ] Un framework completo con router y gestión de estado global integrados para apps grandes
- [ ] Una librería para manipular el DOM de forma imperativa con selectores, eventos y plantillas
- [ ] Una librería de plantillas que genera el HTML en el servidor y lo envía ya renderizado al navegador

> Explicación: React mantiene la UI sincronizada con los datos sin manipular el DOM a mano. Es declarativo: describes cómo debe verse la UI según el estado y React decide cómo actualizarla.

## react-virtual-dom
¿Qué es el Virtual DOM?
tags: frecuente, fundamentos

- [x] Una copia en memoria del DOM que React compara para aplicar solo los cambios mínimos
- [ ] Un DOM paralelo que el navegador renderiza en otro hilo para que React no bloquee la UI
- [ ] Una caché del HTML ya renderizado que evita volver a pedir la página al servidor
- [ ] El DOM real sin sus eventos, lo que lo hace más ligero y rápido de actualizar

> Explicación: React compara el árbol nuevo con el anterior (diffing) y solo toca lo que cambió.

## react-reconciliacion
¿Qué es la reconciliación?
tags: frecuente, fundamentos

- [x] Comparar el árbol viejo con el nuevo para decidir qué se actualiza en el DOM
- [ ] Fusionar el state local de varios componentes en un único objeto global compartido
- [ ] Sincronizar el state de React con el servidor después de cada petición de red
- [ ] Reemplazar siempre todo el DOM real por el árbol nuevo cada vez que cambia el state

> Explicación: Si el tipo de elemento cambia (`div` a `span`) se destruye y recrea el subárbol; si es el mismo, se conserva el nodo y se actualiza lo que cambió. En listas, `key` identifica cada elemento. El motor que lo hace es Fiber (desde React 16), base del concurrent rendering.

## react-jsx
¿Qué es JSX y en qué se convierte?
tags: fundamentos

- [x] En llamadas a funciones (`_jsx` o `React.createElement`) que devuelven objetos
- [ ] En strings de HTML que React inserta en la página usando `innerHTML` al renderizar
- [ ] En plantillas que el navegador interpreta de forma nativa sin ningún compilador
- [ ] En nodos del DOM real creados con `document.createElement` durante el build

> Explicación: El navegador no entiende JSX, así que Babel/SWC lo transforma:
> ```jsx
> <h1 className="title">Hola</h1>
> // se convierte en:
> _jsx("h1", { className: "title", children: "Hola" })
> // (antes: React.createElement("h1", { className: "title" }, "Hola"))
> ```

## react-clase-vs-funcional
¿Para qué siguen siendo necesarios los componentes de clase hoy?
tags: frecuente, fundamentos

- [x] Para los Error Boundaries, porque aún no existe un equivalente con hooks
- [ ] Para usar state local, porque los componentes funcionales no pueden tenerlo
- [ ] Para consumir un Context, porque los hooks no pueden leerlo directamente
- [ ] Para ejecutar efectos al montar, porque los hooks no tienen equivalente

> Explicación: Los funcionales con hooks tienen estado y efectos, con menos código, sin líos con `this` y con lógica reutilizable mediante custom hooks. Las clases solo siguen siendo necesarias para Error Boundaries y código legacy.

## react-props-vs-state
¿Cuál es la diferencia entre props y state?
tags: frecuente, fundamentos

- [x] Las props las pasa el padre y son de solo lectura; el state es interno del componente
- [ ] El state se pasa por props al hijo, que puede modificarlo con `setState` para avisar al padre
- [ ] Las props pueden cambiar durante el render del componente; el state, en cambio, permanece fijo entre renders
- [ ] El state se hereda del componente padre y se comparte con los hijos; las props son locales de cada componente

> Explicación: Las props son datos que el padre le pasa al hijo y no se modifican. El state son datos internos que el componente controla, y al cambiarlo se vuelve a renderizar.

## react-no-mutar-state
¿Por qué no se debe mutar el state directamente?
tags: fundamentos

- [x] React compara referencias con `Object.is`; al mutar, la referencia no cambia
- [ ] React compara el state con `JSON.stringify` en cada render; al mutar, ambas versiones quedan iguales
- [ ] React observa el state con un `Proxy`, pero la mutación directa evita el setter y no se registra
- [ ] React congela el state con `Object.freeze`, así que la mutación lanza un error que rompe el render

> Explicación: Si la referencia sigue igual, React cree que nada cambió. Además rompe `React.memo` y las dependencias de `useEffect`.
> ```jsx
> // Mal
> user.name = "Ana";
> setUser(user);
>
> // Bien: objeto nuevo
> setUser({ ...user, name: "Ana" });
> ```

## react-flujo-unidireccional
¿Qué es el flujo de datos unidireccional en React?
tags: fundamentos

- [x] Los datos bajan del padre al hijo por props y el hijo avisa mediante callbacks
- [ ] El hijo modifica directamente las props del padre y React propaga el cambio hacia abajo en el siguiente render
- [ ] Los datos viajan en ambas direcciones y React sincroniza padre e hijo con binding automático
- [ ] Los datos bajan del padre al hijo por props y el hijo los modifica directamente cuando necesita actualizarlos

> Explicación: El hijo recibe del padre una función (callback) y la llama para avisar algo. Ventaja: es predecible y fácil de depurar. Tradeoff: puede causar prop drilling.

## react-key-indice
¿Por qué no es recomendable usar el índice como `key` en listas dinámicas?
tags: frecuente, fundamentos

- [x] Al reordenar o filtrar cambian los índices y React asocia el state al elemento equivocado
- [ ] React solo acepta keys de tipo string, así que ignora los índices numéricos y usa el orden de la lista
- [ ] Las keys con índice se regeneran en cada render y fuerzan a remontar todos los hijos de la lista
- [ ] Con índices React compara el contenido de cada hijo en profundidad, lo que penaliza el rendimiento

> Explicación: `key` da a cada elemento una identidad estable para saber cuál se agregó, movió o eliminó. Con índices, un input puede "saltar" de fila y se re-renderiza de más. Usa un ID único de los datos; el índice solo vale en listas estáticas. Cambiar la `key` de un componente fuerza que se reinicie desde cero.

## react-controlado-vs-no-controlado
¿Cuál es la diferencia entre un componente controlado y uno no controlado?
tags: frecuente, fundamentos

- [x] En el controlado React guarda el valor en el state; en el no controlado lo guarda el DOM
- [ ] En el controlado el DOM guarda el valor y se lee con una ref; en el no controlado lo guarda el state
- [ ] El controlado usa `defaultValue` y el no controlado usa `value` con `onChange` en cada tecla
- [ ] Ambos guardan el valor en el state; solo cambia si se valida al enviar o al escribir

> Explicación: Controlado: `<input value={name} onChange={e => setName(e.target.value)} />`, con validación en tiempo real pero re-render en cada tecla. No controlado: `<input ref={inputRef} defaultValue="Ana" />`, con menos código y mejor rendimiento pero menos control. React Hook Form usa inputs no controlados por rendimiento.
