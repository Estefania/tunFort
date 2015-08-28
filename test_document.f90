writeBufferInfo=0
    writeBufferData=0.
    nprdbg=0
    iprdbg=-1

    ! parallelize record loop
    ! private copy of NDFS,.. for each thread, combined at end, init with 0.
    
    !$pragma try_schedule
    !$OMP  PARALLEL DO &
    !$OMP   DEFAULT(PRIVATE) &
    !$OMP   SHARED(numReadBuffer,readBufferPointer,readBufferDataI, &
    !$OMP      readBufferDataD,writeBufferHeader,writeBufferInfo, &
    !$OMP      writeBufferData,writeBufferIndices,writeBufferUpdates,globalVector,globalCounter, &
    !$OMP      globalParameter,globalParLabelIndex,globalIndexUsage,backIndexUsage, &
    !$OMP      NAGB,NVGB,NAGBN,ICALCM,ICHUNK,NLOOPN,NRECER,NPRDBG,IPRDBG, &
    !$OMP      NEWITE,CHICUT,LHUBER,CHUBER,ITERAT,NRECPR,MTHRD, &
    !$OMP      DWCUT,CHHUGE,NRECP2,CAUCHY,LFITNP,LFITBB) &
    !$OMP   REDUCTION(+:NDFS,SNDF,DCHI2S,NREJ,NBNDR,NACCF,CHI2F,NDFF) &
    !$OMP   REDUCTION(MAX:NBNDX,NBDRX) &
    !$OMP   REDUCTION(MIN:NREC3) &
    !$OMP SCHEDULE(DYNAMIC,24)


for item in mylist:
    print "{}| {}".format(item.ljust(width),bar(item).ljust(width))
