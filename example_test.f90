      PROGRAM HELLOTHREADS
      INTEGER THREADS , ID
      !$pragma try_schedule
      !$OMP PARALLEL DO &
      !$OMP SCHEDULE(DYNAMIC,24)
      do i=0, 25
        threads = omp_get_num_threads()
        id = omp_get_thread_num()
        PRINT *, "NUM THREADS:", THREADS
        PRINT *, "hello from thread:",id," out of", threads
      end do
      !$OMP END PARALLEL DO
      STOP
      END

