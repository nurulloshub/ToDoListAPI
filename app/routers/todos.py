from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_user
from ..models import Todo, User
from ..schemas import TodoCreate, TodoList, TodoOut, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
async def create_todo(
    payload: TodoCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TodoOut:
    todo = Todo(
        title=payload.title,
        description=payload.description,
        completed=payload.completed,
        user_id=user.id,
    )
    db.add(todo)
    await db.commit()
    await db.refresh(todo)
    return todo


@router.get("", response_model=TodoList)
async def list_todos(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    completed: bool | None = Query(None),
    search: str | None = Query(None, max_length=100),
    sort_by: str = Query("created_at", pattern="^(created_at|title|completed)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TodoList:
    filters = [Todo.user_id == user.id]
    if completed is not None:
        filters.append(Todo.completed == completed)
    if search:
        pattern = f"%{search}%"
        filters.append(or_(Todo.title.ilike(pattern), Todo.description.ilike(pattern)))

    total = await db.scalar(select(func.count(Todo.id)).where(*filters)) or 0

    sort_col = getattr(Todo, sort_by)
    order_clause = asc(sort_col) if order == "asc" else desc(sort_col)

    stmt = (
        select(Todo)
        .where(*filters)
        .order_by(order_clause)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    rows = (await db.scalars(stmt)).all()

    return TodoList(
        data=[TodoOut.model_validate(r) for r in rows],
        page=page,
        limit=limit,
        total=total,
    )


@router.put("/{todo_id}", response_model=TodoOut)
async def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TodoOut:
    todo = await db.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(todo, field, value)

    await db.commit()
    await db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    todo = await db.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    await db.delete(todo)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)